from __future__ import annotations
import os


class Settings:
    # Claudible — OpenAI-compatible endpoint
    ai_api_key: str = os.environ.get("CLAUDIBLE_API_KEY", "")
    ai_base_url: str = os.environ.get("CLAUDIBLE_BASE_URL", "https://claudible.io/v1")
    ai_model: str = os.environ.get("CLAUDIBLE_MODEL", "claude-sonnet-4.6")

    session_ttl_hours: int = 2
    session_sweep_seconds: int = 300
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB


settings = Settings()
