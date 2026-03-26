from __future__ import annotations
from fastapi import APIRouter, HTTPException

from core import session_store, SessionNotFoundError

router = APIRouter(tags=["session"])


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    deleted = await session_store.delete(session_id)
    if not deleted:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return {"deleted": True}
