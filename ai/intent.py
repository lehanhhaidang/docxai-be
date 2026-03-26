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


async def get_format_spec(manifest: dict, user_prompt: str) -> dict:
    """
    Call Claudible (OpenAI-compatible) with the manifest + user prompt.
    Returns a parsed Format Spec dict.
    Raises AIError on API failure or invalid JSON.
    """
    if not settings.ai_api_key:
        raise AIError("CLAUDIBLE_API_KEY is not configured")

    client = OpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
    )

    user_message = (
        f"manifest:\n{json.dumps(manifest, ensure_ascii=False, indent=2)}"
        f"\n\nuser_prompt:\n{user_prompt}"
    )

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
