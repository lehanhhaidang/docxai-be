from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from docx import Document
from io import BytesIO

from core import session_store, SessionNotFoundError

router = APIRouter(tags=["export"])

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class ExportRequest(BaseModel):
    session_id: str


@router.post("/export")
async def export_docx(req: ExportRequest):
    try:
        session = await session_store.get(req.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    # Final validation
    try:
        Document(BytesIO(session.docx_bytes))
    except Exception as exc:
        raise HTTPException(500, f"DOCX is corrupt: {exc}") from exc

    stem = session.filename.rsplit(".", 1)[0] if "." in session.filename else session.filename
    filename = f"{stem}.docx"

    return Response(
        content=session.docx_bytes,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
