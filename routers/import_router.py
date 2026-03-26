from __future__ import annotations
from fastapi import APIRouter, File, HTTPException, UploadFile
from docx import Document
from io import BytesIO

from core import session_store, Session, DocxParseError, settings
from extractor import unzip_docx, parse_document, manifest_to_markdown, manifest_to_html

router = APIRouter(tags=["import"])


def _parse_and_validate(docx_bytes: bytes) -> tuple[dict, str, str]:
    """Parse manifest and sanity-check the file opens with python-docx."""
    files = unzip_docx(docx_bytes)
    doc_xml = files.get("word/document.xml")
    if not doc_xml:
        raise HTTPException(400, "DOCX is missing word/document.xml")
    manifest = parse_document(doc_xml, files.get("word/styles.xml"))
    try:
        Document(BytesIO(docx_bytes))
    except Exception as exc:
        raise HTTPException(400, f"Cannot open DOCX: {exc}") from exc
    return manifest, manifest_to_markdown(manifest), manifest_to_html(manifest)


@router.post("/import")
async def import_docx(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")

    docx_bytes = await file.read()
    if not docx_bytes:
        raise HTTPException(400, "Uploaded file is empty")
    if len(docx_bytes) > settings.max_upload_bytes:
        raise HTTPException(413, "File too large (max 50 MB)")

    try:
        manifest, content_md, preview_html = _parse_and_validate(docx_bytes)
    except DocxParseError as exc:
        raise HTTPException(400, str(exc)) from exc

    session = Session.create(
        filename=file.filename,
        docx_bytes=docx_bytes,
        manifest=manifest,
        content_md=content_md,
        preview_html=preview_html,
    )
    await session_store.add(session)

    return {
        "session_id": session.session_id,
        "manifest": manifest,
        "content_md": content_md,
        "preview_html": preview_html,
    }
