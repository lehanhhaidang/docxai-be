from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from docx import Document
from io import BytesIO

from core import session_store, SessionNotFoundError, SpecValidationError
from ai import validate_format_spec
from executor import apply_format_spec
from routers.template_router import _load_templates

router = APIRouter(tags=["apply"])


class ApplyRequest(BaseModel):
    session_id: str
    format_spec: dict[str, Any] = Field(default_factory=dict)


class ApplyTemplateRequest(BaseModel):
    session_id: str
    template_id: str


@router.post("/apply")
async def apply_spec(req: ApplyRequest):
    try:
        session = await session_store.get(req.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    try:
        validate_format_spec(session.manifest, req.format_spec)
    except SpecValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    try:
        updated_bytes, manifest, content_md, preview_html = apply_format_spec(
            session.docx_bytes, req.format_spec
        )
        # Sanity-check output
        Document(BytesIO(updated_bytes))
    except Exception as exc:
        raise HTTPException(500, f"Failed to apply spec: {exc}") from exc

    session.docx_bytes = updated_bytes
    session.manifest = manifest
    session.content_md = content_md
    session.preview_html = preview_html
    await session_store.update(session)

    return {"manifest": manifest, "preview_html": preview_html}


@router.post("/apply/template")
async def apply_template(req: ApplyTemplateRequest):
    """Apply a predefined template's format_spec to the session."""
    # Load template
    templates = _load_templates()
    template = next((t for t in templates if t["id"] == req.template_id), None)
    if template is None:
        raise HTTPException(404, f"Template '{req.template_id}' not found")

    try:
        session = await session_store.get(req.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    format_spec = template["format_spec"]

    try:
        validate_format_spec(session.manifest, format_spec)
    except SpecValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    try:
        updated_bytes, manifest, content_md, preview_html = apply_format_spec(
            session.docx_bytes, format_spec
        )
        Document(BytesIO(updated_bytes))
    except Exception as exc:
        raise HTTPException(500, f"Failed to apply template: {exc}") from exc

    session.docx_bytes = updated_bytes
    session.manifest = manifest
    session.content_md = content_md
    session.preview_html = preview_html
    await session_store.update(session)

    return {"template_id": req.template_id, "manifest": manifest, "preview_html": preview_html}
