"""Shared Notion client factory."""

from __future__ import annotations

import os
import sys

from notion_client import Client


def get_client() -> Client:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print(
            '{"error": "NOTION_TOKEN 환경변수가 설정되지 않았습니다."}',
            file=sys.stderr,
        )
        raise SystemExit(1)
    return Client(auth=token)
