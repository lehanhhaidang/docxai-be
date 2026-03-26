from __future__ import annotations
import html
from lxml import etree
from extractor.style_reader import parse_styles

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(f"{{{W}}}t"))


def _style_name(ppr) -> str:
    if ppr is None:
        return "Normal"
    ps = ppr.find(f"{{{W}}}pStyle")
    return ps.get(f"{{{W}}}val", "Normal") if ps is not None else "Normal"


def _twips_to_cm(val: str | None) -> float | None:
    try:
        return round(int(val) / 567, 2)
    except (TypeError, ValueError):
        return None


def parse_document(document_xml: bytes, styles_xml: bytes | None = None) -> dict:
    """
    Parse word/document.xml → manifest dict.
    manifest = { meta, styles_defined, blocks[] }
    """
    root = etree.fromstring(document_xml)
    body = root.find(f"{{{W}}}body")
    if body is None:
        return {"meta": {}, "styles_defined": {}, "blocks": []}

    styles_defined = parse_styles(styles_xml) if styles_xml else {}

    # --- meta ---
    meta = {
        "page_size": "A4",
        "margins": {"top": 2.54, "bottom": 2.54, "left": 3.0, "right": 2.0},
        "default_font": "Times New Roman",
        "default_size": 13,
    }
    sect = body.find(f"{{{W}}}sectPr")
    if sect is not None:
        pgMar = sect.find(f"{{{W}}}pgMar")
        if pgMar is not None:
            for side in ("top", "bottom", "left", "right"):
                v = _twips_to_cm(pgMar.get(f"{{{W}}}{side}"))
                if v is not None:
                    meta["margins"][side] = v

    # --- blocks ---
    blocks: list[dict] = []
    bid = 0

    for child in body:
        tag = etree.QName(child.tag).localname

        if tag == "p":
            ppr = child.find(f"{{{W}}}pPr")
            style = _style_name(ppr)
            text = _text(child)
            has_image = bool(child.findall(f".//{{{W}}}drawing"))

            if has_image:
                blocks.append({"id": bid, "type": "image", "caption": text or f"Image {bid}", "note": "preserve"})
            else:
                blocks.append({"id": bid, "type": "paragraph", "style": style, "text": text})
            bid += 1

        elif tag == "tbl":
            rows = child.findall(f".//{{{W}}}tr")
            cols = len(rows[0].findall(f"{{{W}}}tc")) if rows else 0
            blocks.append({"id": bid, "type": "table", "rows": len(rows), "cols": cols, "note": "preserve"})
            bid += 1

    return {"meta": meta, "styles_defined": styles_defined, "blocks": blocks}


def manifest_to_markdown(manifest: dict) -> str:
    lines: list[str] = []
    for block in manifest.get("blocks", []):
        t = block.get("type")
        style = block.get("style", "")
        text = block.get("text", "")

        if t == "image":
            lines.append(f"[IMAGE: {block.get('caption', '')}]")
        elif t == "table":
            lines.append(f"[TABLE: {block['rows']}×{block['cols']} — preserve]")
        elif style.startswith("Heading"):
            level = int(style.split()[-1]) if style.split()[-1].isdigit() else 1
            lines.append("#" * level + " " + text)
        else:
            lines.append(text)

        lines.append("")
    return "\n".join(lines)


def manifest_to_html(manifest: dict) -> str:
    parts: list[str] = ['<div class="doc-preview">']

    for block in manifest.get("blocks", []):
        t = block.get("type")
        style = block.get("style", "")
        safe = html.escape(block.get("text", ""))

        if t == "image":
            parts.append(f'<div class="preview-placeholder preview-image">📷 {html.escape(block.get("caption",""))}</div>')
        elif t == "table":
            parts.append(f'<div class="preview-placeholder preview-table">📊 Table {block["rows"]}×{block["cols"]}</div>')
        elif style.startswith("Heading"):
            lvl = min(int(style.split()[-1]), 6) if style.split()[-1].isdigit() else 1
            parts.append(f'<h{lvl} class="doc-heading doc-h{lvl}">{safe}</h{lvl}>')
        elif style == "TOC":
            parts.append('<div class="preview-placeholder preview-toc">[Mục lục]</div>')
        else:
            if safe.strip():
                parts.append(f'<p class="doc-para">{safe}</p>')

    parts.append("</div>")
    return "\n".join(parts)
