"""Notion property value extractors for JSON output."""

from __future__ import annotations

from typing import Any


def extract_title(prop: dict[str, Any]) -> str:
    parts = prop.get("title", [])
    return "".join(seg.get("plain_text", "") for seg in parts)


def extract_rich_text(prop: dict[str, Any]) -> str:
    parts = prop.get("rich_text", [])
    return "".join(seg.get("plain_text", "") for seg in parts)


def extract_select(prop: dict[str, Any]) -> str | None:
    sel = prop.get("select")
    return sel["name"] if sel else None


def extract_multi_select(prop: dict[str, Any]) -> list[str]:
    return [item["name"] for item in prop.get("multi_select", [])]


def extract_property_value(prop: dict[str, Any]) -> Any:
    """Auto-detect property type and return a JSON-serializable value."""
    ptype = prop.get("type", "")

    if ptype == "title":
        return extract_title(prop)
    if ptype == "rich_text":
        return extract_rich_text(prop)
    if ptype == "number":
        return prop.get("number")
    if ptype == "select":
        return extract_select(prop)
    if ptype == "multi_select":
        return extract_multi_select(prop)
    if ptype == "status":
        status = prop.get("status")
        return status["name"] if status else None
    if ptype == "checkbox":
        return prop.get("checkbox")
    if ptype == "date":
        date_val = prop.get("date")
        return date_val if date_val else None
    if ptype == "url":
        return prop.get("url")
    if ptype == "email":
        return prop.get("email")
    if ptype == "phone_number":
        return prop.get("phone_number")
    if ptype in ("formula", "rollup"):
        inner = prop.get(ptype, {})
        inner_type = inner.get("type", "")
        return inner.get(inner_type)
    if ptype in ("created_time", "last_edited_time"):
        return prop.get(ptype)
    if ptype == "unique_id":
        uid = prop.get("unique_id", {})
        prefix = uid.get("prefix", "")
        number = uid.get("number", 0)
        return f"{prefix}-{number}" if prefix else str(number)

    return None


def flatten_page(page: dict[str, Any], props_filter: list[str] | None = None) -> dict[str, Any]:
    """Flatten a Notion page object into a simple dict for JSON output."""
    props = page.get("properties", {})
    result: dict[str, Any] = {
        "id": page.get("id", ""),
        "url": page.get("url", ""),
    }

    for name, prop in props.items():
        if props_filter and name not in props_filter:
            continue
        result[name] = extract_property_value(prop)

    return result
