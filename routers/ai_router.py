from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import session_store, SessionNotFoundError, AIError
from ai import get_format_spec, validate_format_spec
from core.exceptions import SpecValidationError

router = APIRouter(tags=["ai"])


class IntentRequest(BaseModel):
    session_id: str
    user_prompt: str


@router.post("/ai/intent")
async def ai_intent(req: IntentRequest):
    try:
        session = await session_store.get(req.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    try:
        spec = await get_format_spec(session.manifest, req.user_prompt, session.content_md)
    except AIError as exc:
        raise HTTPException(502, str(exc)) from exc

    # Warn if spec has validation issues but don't block — let /apply validate strictly
    try:
        validate_format_spec(session.manifest, spec)
    except SpecValidationError:
        pass  # Let the caller decide

    return {"format_spec": spec}
