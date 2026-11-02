"""
User profile, product usage and the reaction log. Shares
scan_store's engine (Postgres when DATABASE_URL is set, SQLite otherwise).
"""

import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Session

from models.profile import UserProfile
from services.scan_store import Base, SessionLocal, engine


class ProfileRecord(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True)
    profile_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class UsageRecord(Base):
    __tablename__ = "product_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    product_id = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)


class ReactionRecord(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    product_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    severity = Column(String, nullable=False)  # fine | tingling | redness | peeling
    source = Column(String, nullable=False)  # checkin | scan | quiz
    confirmed = Column(Boolean, default=True)  # scan-detected reactions start unconfirmed


try:
    Base.metadata.create_all(engine)
except Exception as e:
    print(f"[profile_store] Base.metadata.create_all failed, profiles will be unavailable: {e}")


def get_profile(user_id: str) -> UserProfile:
    with SessionLocal() as session:  # type: Session
        record = session.get(ProfileRecord, user_id)
        if record is None:
            return UserProfile(user_id=user_id)
        return UserProfile(**record.profile_json)


def save_profile(profile: UserProfile) -> UserProfile:
    with SessionLocal() as session:
        record = session.get(ProfileRecord, profile.user_id)
        data = profile.model_dump()
        if record is None:
            session.add(ProfileRecord(user_id=profile.user_id, profile_json=data))
        else:
            record.profile_json = data
        session.commit()
    return profile


def start_usage(user_id: str, product_id: str) -> UsageRecord:
    with SessionLocal() as session:
        existing = (
            session.query(UsageRecord)
            .filter(UsageRecord.user_id == user_id, UsageRecord.product_id == product_id, UsageRecord.stopped_at.is_(None))
            .first()
        )
        if existing is not None:
            return existing
        record = UsageRecord(user_id=user_id, product_id=product_id)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def stop_usage(user_id: str, product_id: str) -> bool:
    with SessionLocal() as session:
        records = (
            session.query(UsageRecord)
            .filter(UsageRecord.user_id == user_id, UsageRecord.product_id == product_id, UsageRecord.stopped_at.is_(None))
            .all()
        )
        for r in records:
            r.stopped_at = datetime.datetime.utcnow()
        session.commit()
        return bool(records)


def active_usage(user_id: str) -> list[UsageRecord]:
    with SessionLocal() as session:
        return (
            session.query(UsageRecord)
            .filter(UsageRecord.user_id == user_id, UsageRecord.stopped_at.is_(None))
            .order_by(UsageRecord.started_at.desc())
            .all()
        )


def log_reaction(user_id: str, product_id: str, severity: str, source: str, confirmed: bool = True) -> ReactionRecord:
    with SessionLocal() as session:
        record = ReactionRecord(user_id=user_id, product_id=product_id, severity=severity, source=source, confirmed=confirmed)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def reactions(user_id: str, product_id: str | None = None) -> list[ReactionRecord]:
    with SessionLocal() as session:
        q = session.query(ReactionRecord).filter(ReactionRecord.user_id == user_id)
        if product_id is not None:
            q = q.filter(ReactionRecord.product_id == product_id)
        return q.order_by(ReactionRecord.created_at.desc()).all()


def pending_scan_reactions(user_id: str) -> list[ReactionRecord]:
    with SessionLocal() as session:
        return (
            session.query(ReactionRecord)
            .filter(ReactionRecord.user_id == user_id, ReactionRecord.source == "scan", ReactionRecord.confirmed.is_(False))
            .order_by(ReactionRecord.created_at.desc())
            .all()
        )


def resolve_scan_reaction(user_id: str, reaction_id: int, confirmed: bool) -> ReactionRecord | None:
    """Confirm (keep as a real reaction) or dismiss (delete) a scan-detected one."""
    with SessionLocal() as session:
        record = (
            session.query(ReactionRecord)
            .filter(ReactionRecord.id == reaction_id, ReactionRecord.user_id == user_id)
            .first()
        )
        if record is None:
            return None
        if confirmed:
            record.confirmed = True
            session.commit()
            session.refresh(record)
        else:
            session.delete(record)
            session.commit()
        return record


def cohort_reports(product_id: str, exclude_user: str) -> list[tuple[UserProfile, str]]:
    """Latest confirmed reaction per OTHER user for a product, with that
    user's profile, for the "people like you" signal. Filtering by skin type
    and experience happens in the trust engine."""
    with SessionLocal() as session:
        rows = (
            session.query(ReactionRecord)
            .filter(
                ReactionRecord.product_id == product_id,
                ReactionRecord.user_id != exclude_user,
                ReactionRecord.confirmed.is_(True),
                ReactionRecord.severity != "tingling",
            )
            .order_by(ReactionRecord.created_at.desc())
            .all()
        )
        latest: dict[str, str] = {}
        for r in rows:
            latest.setdefault(r.user_id, r.severity)
        if not latest:
            return []
        profiles = {
            rec.user_id: UserProfile(**rec.profile_json)
            for rec in session.query(ProfileRecord).filter(ProfileRecord.user_id.in_(list(latest))).all()
        }
    return [(profiles[u], sev) for u, sev in latest.items() if u in profiles]
