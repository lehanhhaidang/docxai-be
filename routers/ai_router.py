from __future__ import annotations
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from core import session_store, SessionNotFoundError, AIError
from ai import get_format_spec, validate_format_spec
from ai.prompts import build_system_prompt
from core.exceptions import SpecValidationError
from routers.template_router import _load_templates

router = APIRouter(tags=["ai"])


class IntentRequest(BaseModel):
    session_id: str
    user_prompt: str
    template_id: Optional[str] = None


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

    # Resolve template AI instruction if template_id provided
    ai_instruction: str | None = None
    if req.template_id:
        templates = _load_templates()
        template = next((t for t in templates if t["id"] == req.template_id), None)
        if template is None:
            raise HTTPException(404, f"Template '{req.template_id}' not found")
        ai_instruction = template.get("ai_instruction")

    system_prompt = build_system_prompt(ai_instruction)

    try:
        spec = await get_format_spec(
            session.manifest,
            req.user_prompt,
            session.content_md,
            user_api_key=x_ai_api_key,
            user_provider=x_ai_provider,
            system_prompt=system_prompt,
        )
    except AIError as exc:
        raise HTTPException(502, str(exc)) from exc

    try:
        validate_format_spec(session.manifest, spec)
    except SpecValidationError:
        pass

    return {"format_spec": spec}
