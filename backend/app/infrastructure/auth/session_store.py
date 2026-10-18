from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from sqlalchemy import delete, select

from app.core.config import SESSION_TTL_HOURS
from app.infrastructure.db.models import AuthSession
from app.infrastructure.db.session import get_session


@dataclass(frozen=True)
class StoredSession:
    username: str
    role: str
    csrf_token_hash: str
    expires_at: datetime


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_session(username: str, role: str) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=SESSION_TTL_HOURS)
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)

    with get_session() as db_session:
        db_session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
        db_session.add(
            AuthSession(
                token_hash=_hash(token),
                csrf_token_hash=_hash(csrf_token),
                username=username,
                role=role,
                expires_at=expires_at,
            )
        )
    return token, csrf_token, expires_at


def get_session_by_token(token: str) -> StoredSession | None:
    now = datetime.now(UTC)
    with get_session() as db_session:
        stored = db_session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash == _hash(token),
                AuthSession.expires_at > now,
            )
        )
        if stored is None:
            return None
        return StoredSession(
            username=stored.username,
            role=stored.role,
            csrf_token_hash=stored.csrf_token_hash,
            expires_at=stored.expires_at,
        )


def revoke_session(token: str) -> None:
    with get_session() as db_session:
        db_session.execute(
            delete(AuthSession).where(AuthSession.token_hash == _hash(token))
        )
