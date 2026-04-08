"""Input hardening — defend against LLM-generated malicious inputs."""

from __future__ import annotations

import json
import re


CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
DANGEROUS_UNICODE = {
    0x200B, 0x200C, 0x200D, 0x202E,
    0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF,
}
NOTION_ID_RE = re.compile(r"^[a-f0-9]{32}$")


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "INVALID_INPUT"):
        super().__init__(message)
        self.code = code


def reject_control_chars(value: str) -> None:
    if CONTROL_CHAR_RE.search(value):
        raise ValidationError(f"Control character in input: {value!r}")


def reject_dangerous_unicode(value: str) -> None:
    for ch in value:
        if ord(ch) in DANGEROUS_UNICODE:
            raise ValidationError(f"Dangerous unicode: U+{ord(ch):04X}")


def validate_notion_id(id_str: str) -> str:
    """Validate and normalize a Notion UUID."""
    reject_control_chars(id_str)
    reject_dangerous_unicode(id_str)
    cleaned = id_str.replace("-", "")
    if not NOTION_ID_RE.match(cleaned):
        raise ValidationError(f"Invalid Notion ID: {id_str}")
    return id_str


def validate_json_input(json_str: str) -> dict:
    """Parse and validate JSON string input."""
    reject_control_chars(json_str)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}") from e
