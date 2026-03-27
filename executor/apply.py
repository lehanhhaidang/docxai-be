from __future__ import annotations
from io import BytesIO
from docx import Document

from core.exceptions import SpecValidationError
from extractor.unzip import unzip_docx
from extractor.parser import parse_document, manifest_to_markdown, manifest_to_html
from executor.style_executor import (
    apply_remap_styles, apply_body_font, apply_margins, ensure_paragraph_style,
    apply_line_spacing, reset_direct_paragraph_spacing,
)
from executor.block_executor import (
    iter_body_items, apply_heading_level, apply_alignment,
    insert_paragraph_after, prepend_paragraph, remove_element,
)
from executor.toc_executor import insert_toc


def apply_format_spec(docx_bytes: bytes, spec: dict) -> tuple[bytes, dict, str, str]:
    """
    Apply a validated Format Spec to a .docx file.
    Returns (updated_docx_bytes, updated_manifest, content_md, preview_html).
    """
    # Parse original to map block ids → body items
    orig_files = unzip_docx(docx_bytes)
    orig_manifest = parse_document(
        orig_files["word/document.xml"],
        orig_files.get("word/styles.xml"),
    )

    doc = Document(BytesIO(docx_bytes))
    items = iter_body_items(doc)
    blocks = orig_manifest.get("blocks", [])

    # Build id → item mapping (relies on parser and body being in sync)
    id_to_item: dict[int, dict] = {
        block["id"]: items[i]
        for i, block in enumerate(blocks)
        if i < len(items)
    }
    preserve_ids = {b["id"] for b in blocks if b.get("note") == "preserve"}

    # 1. Style remapping
    if spec.get("remap_styles"):
        apply_remap_styles(doc, spec["remap_styles"])

    # 2. Body font + margins
    if spec.get("font"):
        apply_body_font(doc, spec["font"])
    if spec.get("margins"):
        apply_margins(doc, spec["margins"])

    # 2b. Line spacing + paragraph spacing
    if spec.get("spacing"):
        apply_line_spacing(doc, spec["spacing"])
        reset_direct_paragraph_spacing(doc)

    # 3. Heading levels + paragraph alignment
    heading_ids = {int(h["id"]): int(h["level"]) for h in spec.get("headings", [])}
    default_align = (spec.get("alignment") or {}).get("default")
    heading_align = (spec.get("alignment") or {}).get("headings")

    for block in blocks:
        bid = block["id"]
        if bid in preserve_ids:
            continue
        item = id_to_item.get(bid)
        if not item or item["kind"] != "paragraph":
            continue
        el = item["element"]
        if bid in heading_ids:
            apply_heading_level(doc, el, heading_ids[bid])
        is_heading = block.get("style", "").startswith("Heading") or bid in heading_ids
        if is_heading and heading_align:
            apply_alignment(el, heading_align)
        elif default_align:
            apply_alignment(el, default_align)

    # 4. Delete blocks (reverse order to avoid index shift)
    for bid in sorted((int(b) for b in spec.get("delete_blocks", [])), reverse=True):
        if bid in preserve_ids:
            continue
        item = id_to_item.get(bid)
        if item:
            remove_element(item["element"])

    # 5. Insert blocks
    # cursor tracks the last inserted element per anchor id
    cursor: dict[int, object] = {}
    for ins in spec.get("insert_blocks", []):
        after_id = int(ins["after_id"])
        style_name = ins.get("style", "Normal")
        text = ins.get("text", "")
        ensure_paragraph_style(doc, style_name)

        if after_id == -1:
            anchor = cursor.get(-1)
            new_el = (
                insert_paragraph_after(anchor, text, style_name)
                if anchor is not None
                else prepend_paragraph(doc, text, style_name)
            )
        else:
            anchor = cursor.get(after_id) or id_to_item[after_id]["element"]
            new_el = insert_paragraph_after(anchor, text, style_name)

        cursor[after_id] = new_el

    # 6. TOC
    toc_spec = spec.get("toc")
    if toc_spec:
        before_id = int(toc_spec.get("insert_before_id", -1))
        before_el = id_to_item[before_id]["element"] if before_id != -1 and before_id in id_to_item else None
        insert_toc(doc, before_el)

    # Save + reparse
    buf = BytesIO()
    doc.save(buf)
    updated_bytes = buf.getvalue()

    updated_files = unzip_docx(updated_bytes)
    updated_manifest = parse_document(
        updated_files["word/document.xml"],
        updated_files.get("word/styles.xml"),
    )
    return (
        updated_bytes,
        updated_manifest,
        manifest_to_markdown(updated_manifest),
        manifest_to_html(updated_manifest),
    )
