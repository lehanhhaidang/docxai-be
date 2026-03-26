from __future__ import annotations
import re


def markdown_to_blocks(md_content: str) -> list[dict]:
    """
    Parse plain Markdown text into a list of block dicts.
    Each block: { type, style, text }
    """
    blocks: list[dict] = []
    for line in md_content.splitlines():
        line = line.rstrip()
        if not line:
            continue

        # ATX headings: ## Title
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            blocks.append({"type": "heading", "style": f"Heading {level}", "text": m.group(2).strip()})
            continue

        # Unordered list: - item or * item
        m = re.match(r"^[-*+]\s+(.*)", line)
        if m:
            blocks.append({"type": "paragraph", "style": "List Paragraph", "text": "• " + m.group(1).strip()})
            continue

        # Ordered list: 1. item
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            blocks.append({"type": "paragraph", "style": "List Paragraph", "text": line.strip()})
            continue

        # Normal paragraph
        blocks.append({"type": "paragraph", "style": "Normal", "text": line})

    return blocks


def blocks_to_format_spec(blocks: list[dict], insert_after_id: int) -> dict:
    """Convert a list of blocks into a Format Spec insert_blocks array."""
    return {
        "insert_blocks": [
            {
                "after_id": insert_after_id,
                "type": block["type"],
                "style": block["style"],
                "text": block["text"],
            }
            for block in blocks
        ]
    }
