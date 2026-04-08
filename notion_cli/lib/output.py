"""JSON-First output module. stdout = data only, stderr = logs."""

from __future__ import annotations

import json
import sys


def output(data: object, fmt: str = "json") -> None:
    if fmt == "ndjson":
        items = data if isinstance(data, list) else [data]
        for item in items:
            sys.stdout.write(json.dumps(item, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def output_error(code: str, message: str) -> None:
    sys.stdout.write(
        json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False) + "\n"
    )
