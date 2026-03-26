from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from core.config import settings
from core.exceptions import SessionNotFoundError


@dataclass
class Session:
    session_id: str
    filename: str
    docx_bytes: bytes
    manifest: dict
    content_md: str
    preview_html: str
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.last_accessed = datetime.now(timezone.utc)

    @staticmethod
    def create(filename: str, docx_bytes: bytes, manifest: dict, content_md: str, preview_html: str) -> "Session":
        return Session(
            session_id=str(uuid4()),
            filename=filename,
            docx_bytes=docx_bytes,
            manifest=manifest,
            content_md=content_md,
            preview_html=preview_html,
        )


class SessionStore:
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def add(self, session: Session) -> None:
        async with self._lock:
            self._store[session.session_id] = session

    async def get(self, session_id: str) -> Session:
        async with self._lock:
            session = self._store.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{session_id}' not found or expired")
        session.touch()
        return session

    async def update(self, session: Session) -> None:
        async with self._lock:
            self._store[session.session_id] = session

    async def delete(self, session_id: str) -> bool:
        async with self._lock:
            return self._store.pop(session_id, None) is not None

    async def sweep_expired(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.session_ttl_hours)
        async with self._lock:
            expired = [k for k, v in self._store.items() if v.last_accessed < cutoff]
            for k in expired:
                del self._store[k]
        return len(expired)


# Singleton shared across the app
session_store = SessionStore()
