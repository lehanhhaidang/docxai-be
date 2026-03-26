from __future__ import annotations
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from core import session_store, SessionNotFoundError, AIError
from ai import get_format_spec, validate_format_spec
from core.exceptions import SpecValidationError

router = APIRouter(tags=["ai"])


class IntentRequest(BaseModel):
    session_id: str
    user_prompt: str


@router.post("/ai/intent")
async def ai_intent(
    req: IntentRequest,
    x_ai_api_key: str | None = Header(default=None),
    x_ai_provider: str | None = Header(default=None),
):
    try:
        session = await session_store.get(req.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    try:
        spec = await get_format_spec(
            session.manifest,
            req.user_prompt,
            session.content_md,
            user_api_key=x_ai_api_key,
            user_provider=x_ai_provider,
        )
    except AIError as exc:
        raise HTTPException(502, str(exc)) from exc

    try:
        validate_format_spec(session.manifest, spec)
    except SpecValidationError:
        pass

    return {"format_spec": spec}
