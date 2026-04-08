"""Typer CLI entry-point for notion-cli."""

from __future__ import annotations

import json
import sys
from typing import Annotated, Optional

import typer
from notion_client.errors import APIResponseError

from notion_cli.client import get_client
from notion_cli.formatters import extract_title, flatten_page

app = typer.Typer(help="notion — Minimal Notion CLI for AI agents", add_completion=False)
page_app = typer.Typer(help="Page operations")
db_app = typer.Typer(help="Database operations")
app.add_typer(page_app, name="page")
app.add_typer(db_app, name="db")


def _dump(obj: object) -> None:
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    print()


def _handle_api_error(exc: APIResponseError) -> None:
    _dump({"error": exc.code, "status": exc.status, "message": str(exc)})
    raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# notion search
# ---------------------------------------------------------------------------

@app.command()
def search(
    query: Annotated[str, typer.Argument(help="검색 키워드")],
    type: Annotated[Optional[str], typer.Option("--type", "-t", help="page 또는 db")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="최대 결과 수")] = 20,
) -> None:
    """워크스페이스에서 페이지/데이터베이스를 검색합니다."""
    client = get_client()

    kwargs: dict = {"query": query, "page_size": min(limit, 100)}
    if type in ("page", "db", "database"):
        value = "data_source" if type in ("db", "database") else "page"
        kwargs["filter"] = {"property": "object", "value": value}

    try:
        response = client.search(**kwargs)
    except APIResponseError as exc:
        _handle_api_error(exc)
    results = []
    for item in response.get("results", [])[:limit]:
        obj_type = item.get("object", "")
        if obj_type == "page":
            props = item.get("properties", {})
            title_prop = next((v for v in props.values() if v.get("type") == "title"), None)
            title = extract_title(title_prop) if title_prop else ""
        else:
            title_arr = item.get("title", [])
            title = "".join(seg.get("plain_text", "") for seg in title_arr)

        results.append({
            "id": item.get("id", ""),
            "object": obj_type,
            "title": title,
            "url": item.get("url", ""),
        })

    _dump(results)


# ---------------------------------------------------------------------------
# notion page get
# ---------------------------------------------------------------------------

@page_app.command("get")
def page_get(
    page_id: Annotated[str, typer.Argument(help="페이지 UUID")],
    props: Annotated[Optional[str], typer.Option("--props", "-p", help="쉼표 구분 프로퍼티 이름")] = None,
) -> None:
    """페이지 프로퍼티를 JSON으로 출력합니다."""
    client = get_client()
    try:
        page = client.pages.retrieve(page_id=page_id)
    except APIResponseError as exc:
        _handle_api_error(exc)
    props_filter = [p.strip() for p in props.split(",")] if props else None
    _dump(flatten_page(page, props_filter))


# ---------------------------------------------------------------------------
# notion page create
# ---------------------------------------------------------------------------

@page_app.command("create")
def page_create(
    title: Annotated[str, typer.Option("--title", "-t", help="페이지 제목")],
    parent_page: Annotated[Optional[str], typer.Option("--parent-page", help="부모 페이지 UUID")] = None,
    parent_db: Annotated[Optional[str], typer.Option("--parent-db", help="부모 데이터베이스 UUID")] = None,
    body: Annotated[Optional[str], typer.Option("--body", "-b", help="본문 텍스트 (단락)")] = None,
    props_json: Annotated[Optional[str], typer.Option("--props-json", help="추가 프로퍼티 JSON 문자열")] = None,
) -> None:
    """새 페이지를 생성합니다."""
    if not parent_page and not parent_db:
        print('{"error": "--parent-page 또는 --parent-db 중 하나를 지정하세요."}', file=sys.stderr)
        raise typer.Exit(code=1)

    client = get_client()

    parent: dict
    if parent_db:
        parent = {"database_id": parent_db}
    else:
        parent = {"page_id": parent_page}

    properties: dict = {"title": {"title": [{"text": {"content": title}}]}}
    if props_json:
        extra = json.loads(props_json)
        properties.update(extra)

    children: list[dict] = []
    if body:
        for paragraph in body.split("\n\n"):
            if paragraph.strip():
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": paragraph.strip()}}]},
                })

    try:
        response = client.pages.create(parent=parent, properties=properties, children=children or None)
    except APIResponseError as exc:
        _handle_api_error(exc)
    _dump({"id": response.get("id", ""), "url": response.get("url", "")})


# ---------------------------------------------------------------------------
# notion db query
# ---------------------------------------------------------------------------

@db_app.command("query")
def db_query(
    database_id: Annotated[str, typer.Argument(help="데이터베이스 UUID")],
    filter: Annotated[Optional[str], typer.Option("--filter", "-f", help="필터 JSON 문자열")] = None,
    sort: Annotated[Optional[str], typer.Option("--sort", "-s", help="정렬 (property:direction, 예: Date:descending)")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="최대 결과 수")] = 100,
    props: Annotated[Optional[str], typer.Option("--props", "-p", help="쉼표 구분 프로퍼티 이름")] = None,
) -> None:
    """데이터베이스를 쿼리하고 결과를 JSON으로 출력합니다."""
    client = get_client()

    kwargs: dict = {"database_id": database_id, "page_size": min(limit, 100)}

    if filter:
        kwargs["filter"] = json.loads(filter)

    if sort:
        sorts = []
        for part in sort.split(","):
            pieces = part.strip().split(":")
            prop_name = pieces[0]
            direction = pieces[1] if len(pieces) > 1 else "ascending"
            sorts.append({"property": prop_name, "direction": direction})
        kwargs["sorts"] = sorts

    props_filter = [p.strip() for p in props.split(",")] if props else None

    results = []
    cursor: str | None = None
    collected = 0

    while collected < limit:
        if cursor:
            kwargs["start_cursor"] = cursor
        kwargs["page_size"] = min(limit - collected, 100)

        try:
            response = client.databases.query(**kwargs)
        except APIResponseError as exc:
            _handle_api_error(exc)
        for page in response.get("results", []):
            results.append(flatten_page(page, props_filter))
            collected += 1
            if collected >= limit:
                break

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    _dump(results)


# ---------------------------------------------------------------------------
# notion db schema
# ---------------------------------------------------------------------------

@db_app.command("schema")
def db_schema(
    database_id: Annotated[str, typer.Argument(help="데이터베이스 UUID")],
) -> None:
    """데이터베이스 스키마(프로퍼티 정의)를 JSON으로 출력합니다."""
    client = get_client()
    try:
        db = client.databases.retrieve(database_id=database_id)
    except APIResponseError as exc:
        _handle_api_error(exc)

    schema = {}
    for name, prop in db.get("properties", {}).items():
        entry: dict = {"type": prop.get("type", "")}
        if prop.get("type") == "select":
            entry["options"] = [opt["name"] for opt in prop.get("select", {}).get("options", [])]
        elif prop.get("type") == "multi_select":
            entry["options"] = [opt["name"] for opt in prop.get("multi_select", {}).get("options", [])]
        elif prop.get("type") == "status":
            entry["options"] = [opt["name"] for opt in prop.get("status", {}).get("options", [])]
        schema[name] = entry

    title_arr = db.get("title", [])
    title = "".join(seg.get("plain_text", "") for seg in title_arr)

    _dump({"id": db.get("id", ""), "title": title, "properties": schema})


if __name__ == "__main__":
    app()
