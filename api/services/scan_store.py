"""
Scan history persistence. Uses Postgres (Supabase) when DATABASE_URL is set —
required on serverless hosts like Vercel, whose filesystem is ephemeral and
can't hold a SQLite file across requests. Falls back to a local SQLite file
for development, where a persistent disk is just there.
"""

import datetime
import os

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
SIGNIFICANCE_THRESHOLD = 0.08  # normalised-score delta below this reads as "about the same"

if DATABASE_URL:
    # Supabase/Postgres connection strings use the `postgresql://` scheme
    # already, but normalise the legacy `postgres://` form just in case.
    normalised_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(normalised_url, pool_pre_ping=True)
else:
    SCAN_DB_PATH = os.getenv("SCAN_DB_PATH", "./scan_history.db")
    engine = create_engine(f"sqlite:///{SCAN_DB_PATH}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ScanRecord(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    metrics_json = Column(JSON, nullable=False)
    trust_score = Column(Float, nullable=False)
    advice_json = Column(JSON, nullable=False)


try:
    Base.metadata.create_all(engine)
except Exception as e:
    # Runs at import time, imported by main.py before the FastAPI app object
    # even exists — a failure here (e.g. an unwritable filesystem on some
    # hosts) must not take down chat/health/tts, which don't touch SQLite at
    # all. Scan/history/auth endpoints will fail per-request instead, which
    # FastAPI turns into a scoped 500 rather than the whole app refusing to boot.
    print(f"[scan_store] Base.metadata.create_all failed, scan history will be unavailable: {e}")


def save_scan(user_id: str, metrics: list[dict], trust_score: float, advice: list[dict]) -> ScanRecord:
    with SessionLocal() as session:  # type: Session
        record = ScanRecord(
            user_id=user_id,
            metrics_json=metrics,
            trust_score=trust_score,
            advice_json=advice,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def get_last_scan(user_id: str) -> ScanRecord | None:
    with SessionLocal() as session:
        return (
            session.query(ScanRecord)
            .filter(ScanRecord.user_id == user_id)
            .order_by(ScanRecord.created_at.desc())
            .first()
        )


def get_scan_history(user_id: str, limit: int = 10) -> list[ScanRecord]:
    with SessionLocal() as session:
        return (
            session.query(ScanRecord)
            .filter(ScanRecord.user_id == user_id)
            .order_by(ScanRecord.created_at.desc())
            .limit(limit)
            .all()
        )


def delete_scan(scan_id: int, user_id: str) -> bool:
    """Scoped to user_id so one user can't delete another's scan by guessing an id."""
    with SessionLocal() as session:
        record = (
            session.query(ScanRecord)
            .filter(ScanRecord.id == scan_id, ScanRecord.user_id == user_id)
            .first()
        )
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True


def compute_deltas(previous_metrics: list[dict], current_metrics: list[dict]) -> dict:
    """Only report a change as real if it exceeds SIGNIFICANCE_THRESHOLD.
    Two scans differing by noise are reported as "about the same" — never as
    improvement. Overstating progress is exactly the failure mode the trust
    engine exists to prevent."""
    previous_by_name = {m["name"]: m for m in previous_metrics}
    deltas = {}
    for metric in current_metrics:
        name = metric["name"]
        previous = previous_by_name.get(name)
        if previous is None:
            continue
        change = previous["normalised"] - metric["normalised"]  # positive = improved (less severe)
        if abs(change) < SIGNIFICANCE_THRESHOLD:
            deltas[name] = {"direction": "about_the_same", "change": round(change, 3)}
        elif change > 0:
            deltas[name] = {"direction": "improved", "change": round(change, 3)}
        else:
            deltas[name] = {"direction": "worsened", "change": round(change, 3)}
    return deltas
