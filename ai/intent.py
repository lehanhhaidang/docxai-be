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


async def get_format_spec(manifest: dict, user_prompt: str, content_md: str = "") -> dict:
    """
    Call Claudible (OpenAI-compatible) with manifest + content_md + user prompt.
    Returns a parsed Format Spec dict.
    Raises AIError on API failure or invalid JSON.
    """
    if not settings.ai_api_key:
        raise AIError("CLAUDIBLE_API_KEY is not configured")

    client = OpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
    )

    # Build user message: manifest + content context + user request
    user_message_parts = [
        f"manifest:\n{json.dumps(manifest, ensure_ascii=False, indent=2)}",
    ]
    if content_md.strip():
        # Truncate if too long to avoid blowing context window
        md_snippet = content_md[:6000] + ("\n[... truncated ...]" if len(content_md) > 6000 else "")
        user_message_parts.append(f"content_md (nội dung hiện tại của document):\n{md_snippet}")
    user_message_parts.append(f"user_prompt:\n{user_prompt}")

    user_message = "\n\n".join(user_message_parts)

    try:
        response = client.chat.completions.create(
            model=settings.ai_model,
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
