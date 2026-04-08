"""Field masking for context window discipline."""

from __future__ import annotations

from typing import Any


def apply_fields(data: Any, fields_str: str | None) -> Any:
    """Keep only specified fields. Reduces token usage by ~90%."""
    if not fields_str:
        return data
    fields = {f.strip() for f in fields_str.split(",")}
    # Always keep 'id' for reference
    fields.add("id")

    def pick(obj: dict) -> dict:
        return {k: v for k, v in obj.items() if k in fields}

    if isinstance(data, list):
        return [pick(item) for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return pick(data)
    return data
