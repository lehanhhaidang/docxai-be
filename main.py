from __future__ import annotations
import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import session_store, settings
from routers import (
    import_router, apply_router, ai_router,
    ingest_router, export_router, session_router,
    template_router,
)


async def _session_sweeper() -> None:
    """Background task: remove expired sessions every N seconds."""
    while True:
        await asyncio.sleep(settings.session_sweep_seconds)
        await session_store.sweep_expired()


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_session_sweeper())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="DocFlow API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_router)
app.include_router(apply_router)
app.include_router(ai_router)
app.include_router(ingest_router)
app.include_router(export_router)
app.include_router(session_router)
app.include_router(template_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
