from __future__ import annotations
from core.exceptions import SpecValidationError


def validate_format_spec(manifest: dict, spec: dict) -> None:
    """
    Raise SpecValidationError if the spec references unknown block ids or styles.
    Mutates nothing.
    """
    blocks = manifest.get("blocks", [])
    block_ids = {b["id"] for b in blocks}
    preserve_ids = {b["id"] for b in blocks if b.get("note") == "preserve"}
    known_styles = set(manifest.get("styles_defined", {}).keys())
    # Styles being defined in this same spec are also valid targets
    new_styles = set(spec.get("remap_styles", {}).keys())
    valid_styles = known_styles | new_styles

    for h in spec.get("headings", []):
        bid = int(h["id"])
        if bid not in block_ids:
            raise SpecValidationError(f"headings: unknown block id {bid}")
        if bid in preserve_ids:
            raise SpecValidationError(f"headings: block {bid} is preserved")

    for bid in spec.get("delete_blocks", []):
        if int(bid) not in block_ids:
            raise SpecValidationError(f"delete_blocks: unknown block id {bid}")
        if int(bid) in preserve_ids:
            raise SpecValidationError(f"delete_blocks: block {bid} is preserved")

    for ins in spec.get("insert_blocks", []):
        after_id = int(ins["after_id"])
        if after_id != -1 and after_id not in block_ids:
            raise SpecValidationError(f"insert_blocks: unknown after_id {after_id}")
        style = ins.get("style")
        if style and style not in valid_styles:
            raise SpecValidationError(f"insert_blocks: unknown style '{style}' — add it to remap_styles first")

    toc = spec.get("toc")
    if toc:
        before_id = int(toc.get("insert_before_id", -1))
        if before_id != -1 and before_id not in block_ids:
            raise SpecValidationError(f"toc: unknown insert_before_id {before_id}")

    spacing = spec.get("spacing")
    if spacing is not None:
        if not isinstance(spacing, dict):
            raise SpecValidationError("spacing: must be an object")
        line = spacing.get("line")
        if line is not None and line not in (1.0, 1.15, 1.5, 2.0):
            raise SpecValidationError(f"spacing.line: invalid value {line!r} — must be 1.0, 1.15, 1.5, or 2.0")
        for field in ("before_pt", "after_pt"):
            val = spacing.get(field)
            if val is not None and (not isinstance(val, (int, float)) or val < 0):
                raise SpecValidationError(f"spacing.{field}: must be a non-negative number")
