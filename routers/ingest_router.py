from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import session_store, SessionNotFoundError
from ingestion import markdown_to_blocks, blocks_to_format_spec

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    session_id: str
    md_content: str
    insert_after_id: int = -1


@router.post("/ingest/md")
async def ingest_markdown(req: IngestRequest):
    try:
        session = await session_store.get(req.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    block_ids = {b["id"] for b in session.manifest.get("blocks", [])}
    if req.insert_after_id != -1 and req.insert_after_id not in block_ids:
        raise HTTPException(400, f"insert_after_id {req.insert_after_id} not found in manifest")

    blocks = markdown_to_blocks(req.md_content)
    spec = blocks_to_format_spec(blocks, req.insert_after_id)
    return {"format_spec": spec}
