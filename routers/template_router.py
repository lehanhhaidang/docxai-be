from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(tags=["templates"])

TEMPLATES_PATH = Path(__file__).parent.parent / "templates" / "templates.json"


def _load_templates() -> list[dict]:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/templates")
async def list_templates():
    """List all available templates (without format_spec detail)."""
    templates = _load_templates()
    return {
        "templates": [
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
            }
            for t in templates
        ]
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get full template including format_spec."""
    templates = _load_templates()
    for t in templates:
        if t["id"] == template_id:
            return t
    from fastapi import HTTPException
    raise HTTPException(404, f"Template '{template_id}' not found")
