from __future__ import annotations
import json
from openai import OpenAI, APIError

from core.config import settings
from core.exceptions import AIError
from ai.prompts import SYSTEM_PROMPT


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def _make_client(user_api_key: str | None, user_provider: str | None) -> OpenAI:
    """
    Build an OpenAI-compatible client.
    Priority: user-supplied key > server claudible key.
    Supported providers: "anthropic" | "openai" | "claudible" (default)
    """
    if user_api_key:
        provider = (user_provider or "openai").lower()
        if provider == "anthropic":
            return OpenAI(
                api_key=user_api_key,
                base_url="https://api.anthropic.com/v1",
            )
        elif provider == "openai":
            return OpenAI(api_key=user_api_key)
        else:
            # Treat as generic OpenAI-compatible
            return OpenAI(api_key=user_api_key)

    # Fallback: server claudible key
    if not settings.ai_api_key:
        raise AIError("No AI API key configured. Please provide your own API key.")
    return OpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
    )


def _resolve_model(user_provider: str | None) -> str:
    provider = (user_provider or "").lower()
    if provider == "anthropic":
        return "claude-sonnet-4-20250514"
    elif provider == "openai":
        return "gpt-4o"
    return settings.ai_model  # claudible default


async def get_format_spec(
    manifest: dict,
    user_prompt: str,
    content_md: str = "",
    user_api_key: str | None = None,
    user_provider: str | None = None,
) -> dict:
    """
    Call AI with manifest + content_md + user prompt.
    Uses user-supplied key/provider when available, falls back to server key.
    Raises AIError on API failure or invalid JSON.
    """
    client = _make_client(user_api_key, user_provider)
    model = _resolve_model(user_provider if user_api_key else None)

    user_message_parts = [
        f"manifest:\n{json.dumps(manifest, ensure_ascii=False, indent=2)}",
    ]
    if content_md.strip():
        md_snippet = content_md[:6000] + ("\n[... truncated ...]" if len(content_md) > 6000 else "")
        user_message_parts.append(f"content_md (nội dung hiện tại của document):\n{md_snippet}")
    user_message_parts.append(f"user_prompt:\n{user_prompt}")

    user_message = "\n\n".join(user_message_parts)

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        raw = _strip_fences(response.choices[0].message.content or "")
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIError(f"AI returned invalid JSON: {exc}") from exc
    except APIError as exc:
        raise AIError(f"AI API error: {exc}") from exc
