"""
Minimal user record — just enough to give a signed-in user a stable id so
their scan history follows them across devices. Sign-in is optional: the
app's anonymous local-id flow (see frontend's getOrCreateUserId) keeps
working unchanged for anyone who never signs in. Same SQLite file as
scan_store.py, separate table.
"""

import datetime

from sqlalchemy import Column, DateTime, String

from services.scan_store import Base, SessionLocal, engine


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Google "sub" claim
    email = Column(String, nullable=True)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


try:
    Base.metadata.create_all(engine)
except Exception as e:
    print(f"[auth_store] Base.metadata.create_all failed, sign-in persistence will be unavailable: {e}")


def upsert_user(user_id: str, email: str | None, name: str | None, picture: str | None) -> UserRecord:
    with SessionLocal() as session:
        record = session.get(UserRecord, user_id)
        if record is None:
            record = UserRecord(id=user_id, email=email, name=name, picture=picture)
            session.add(record)
        else:
            record.email = email
            record.name = name
            record.picture = picture
        session.commit()
        session.refresh(record)
        return record
