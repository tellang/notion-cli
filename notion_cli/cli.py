"""Typer CLI entry-point for notion-cli — Agent DX 7 principles applied."""

from __future__ import annotations

import json
import sys
from typing import Annotated, Optional

import typer
from notion_client.errors import APIResponseError

from notion_cli.client import get_client
from notion_cli.formatters import extract_title, flatten_page
from notion_cli.lib.fields import apply_fields
from notion_cli.lib.output import output, output_error
from notion_cli.lib.validate import ValidationError, validate_json_input, validate_notion_id
from notion_cli.schemas import SCHEMAS

app = typer.Typer(help="notion — Notion API CLI for AI agents", add_completion=False)
page_app = typer.Typer(help="Page operations")
db_app = typer.Typer(help="Database operations")
block_app = typer.Typer(help="Block operations")
comment_app = typer.Typer(help="Comment operations")
user_app = typer.Typer(help="User operations")
app.add_typer(page_app, name="page")
app.add_typer(db_app, name="db")
app.add_typer(block_app, name="block")
app.add_typer(comment_app, name="comment")
app.add_typer(user_app, name="user")


def _handle_api_error(exc: APIResponseError) -> None:
    output_error(exc.code, str(exc))
    raise typer.Exit(code=1)


def _handle_validation_error(exc: ValidationError) -> None:
    output_error(exc.code, str(exc))
    raise typer.Exit(code=1)


def _build_paragraphs(text: str) -> list[dict]:
    children: list[dict] = []
    for paragraph in text.split("\n\n"):
        if paragraph.strip():
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": paragraph.strip()}}]},
            })
    return children


# ---------------------------------------------------------------------------
# notion schema — Runtime Schema Introspection (Principle 3)
# ---------------------------------------------------------------------------

@app.command()
def schema(
    command: Annotated[Optional[str], typer.Argument(help="커맨드 이름 (예: 'page get', 'db query')")] = None,
) -> None:
    """커맨드별 파라미터 스키마를 JSON으로 반환합니다."""
    if not command:
        commands = [{"command": k, "description": v["description"]} for k, v in SCHEMAS.items()]
        output(commands)
        return
    s = SCHEMAS.get(command)
    if not s:
        output_error("NOT_FOUND", f"Unknown command: {command}")
        raise typer.Exit(code=1)
    output(s)


# ---------------------------------------------------------------------------
# notion search
# ---------------------------------------------------------------------------

@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search keyword")],
    type: Annotated[Optional[str], typer.Option("--type", "-t", help="page or db")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 20,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated fields")] = None,
) -> None:
    """Search workspace for pages and databases."""
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

    output(apply_fields(results, fields))


# ---------------------------------------------------------------------------
# notion page get
# ---------------------------------------------------------------------------

@page_app.command("get")
def page_get(
    page_id: Annotated[str, typer.Argument(help="Page UUID")],
    props: Annotated[Optional[str], typer.Option("--props", "-p", help="Comma-separated property names")] = None,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """Retrieve page properties as JSON."""
    try:
        validate_notion_id(page_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    client = get_client()
    try:
        page = client.pages.retrieve(page_id=page_id)
    except APIResponseError as exc:
        _handle_api_error(exc)

    props_filter = [p.strip() for p in props.split(",")] if props else None
    output(apply_fields(flatten_page(page, props_filter), fields))


# ---------------------------------------------------------------------------
# notion page create
# ---------------------------------------------------------------------------

@page_app.command("create")
def page_create(
    title: Annotated[str, typer.Option("--title", "-t", help="Page title")],
    parent_page: Annotated[Optional[str], typer.Option("--parent-page", help="Parent page UUID")] = None,
    parent_db: Annotated[Optional[str], typer.Option("--parent-db", help="Parent database UUID")] = None,
    body: Annotated[Optional[str], typer.Option("--body", "-b", help="Body text (paragraphs)")] = None,
    props_json: Annotated[Optional[str], typer.Option("--props-json", help="Additional properties JSON")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """Create a new page."""
    if not parent_page and not parent_db:
        output_error("MISSING_PARAM", "--parent-page or --parent-db required")
        raise typer.Exit(code=1)

    parent: dict
    if parent_db:
        parent = {"database_id": parent_db}
    else:
        parent = {"page_id": parent_page}

    properties: dict = {"title": {"title": [{"text": {"content": title}}]}}
    if props_json:
        try:
            properties.update(validate_json_input(props_json))
        except ValidationError as exc:
            _handle_validation_error(exc)

    children = _build_paragraphs(body) if body else []

    if dry_run:
        output({"dryRun": True, "action": "pages.create", "parent": parent, "properties": properties, "children_count": len(children)})
        return

    client = get_client()
    try:
        response = client.pages.create(parent=parent, properties=properties, children=children or None)
    except APIResponseError as exc:
        _handle_api_error(exc)
    output(apply_fields({"id": response.get("id", ""), "url": response.get("url", "")}, fields))


# ---------------------------------------------------------------------------
# notion page update
# ---------------------------------------------------------------------------

@page_app.command("update")
def page_update(
    page_id: Annotated[str, typer.Argument(help="Page UUID")],
    props_json: Annotated[Optional[str], typer.Option("--props-json", help="Properties JSON")] = None,
    archive: Annotated[Optional[bool], typer.Option("--archive", help="Archive")] = None,
    trash: Annotated[Optional[bool], typer.Option("--trash", help="Move to trash")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """Update page properties."""
    try:
        validate_notion_id(page_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    kwargs: dict = {"page_id": page_id}
    if props_json:
        try:
            kwargs["properties"] = validate_json_input(props_json)
        except ValidationError as exc:
            _handle_validation_error(exc)
    if archive is not None:
        kwargs["archived"] = archive
    if trash is not None:
        kwargs["in_trash"] = trash

    if dry_run:
        output({"dryRun": True, "action": "pages.update", **kwargs})
        return

    client = get_client()
    try:
        page = client.pages.update(**kwargs)
    except APIResponseError as exc:
        _handle_api_error(exc)
    output(apply_fields(flatten_page(page), fields))


# ---------------------------------------------------------------------------
# notion db query
# ---------------------------------------------------------------------------

@db_app.command("query")
def db_query(
    database_id: Annotated[str, typer.Argument(help="Database or data_source UUID")],
    filter: Annotated[Optional[str], typer.Option("--filter", "-f", help="Filter JSON")] = None,
    sort: Annotated[Optional[str], typer.Option("--sort", "-s", help="Sort (property:direction)")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 100,
    props: Annotated[Optional[str], typer.Option("--props", "-p", help="Comma-separated property names")] = None,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """Query a database and return results as JSON."""
    try:
        validate_notion_id(database_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    client = get_client()

    kwargs: dict = {"data_source_id": database_id, "page_size": min(limit, 100)}

    if filter:
        try:
            kwargs["filter"] = validate_json_input(filter)
        except ValidationError as exc:
            _handle_validation_error(exc)

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
            response = client.data_sources.query(**kwargs)
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

    output(apply_fields(results, fields))


# ---------------------------------------------------------------------------
# notion db schema
# ---------------------------------------------------------------------------

@db_app.command("schema")
def db_schema(
    database_id: Annotated[str, typer.Argument(help="Database or data_source UUID")],
) -> None:
    """Retrieve database schema (property definitions)."""
    try:
        validate_notion_id(database_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    client = get_client()
    try:
        db = client.data_sources.retrieve(data_source_id=database_id)
    except APIResponseError:
        try:
            db = client.databases.retrieve(database_id=database_id)
        except APIResponseError as exc:
            _handle_api_error(exc)

    props_schema = {}
    for name, prop in db.get("properties", {}).items():
        entry: dict = {"type": prop.get("type", "")}
        if prop.get("type") == "select":
            entry["options"] = [opt["name"] for opt in prop.get("select", {}).get("options", [])]
        elif prop.get("type") == "multi_select":
            entry["options"] = [opt["name"] for opt in prop.get("multi_select", {}).get("options", [])]
        elif prop.get("type") == "status":
            entry["options"] = [opt["name"] for opt in prop.get("status", {}).get("options", [])]
        props_schema[name] = entry

    title_arr = db.get("title", [])
    title = "".join(seg.get("plain_text", "") for seg in title_arr)

    output({"id": db.get("id", ""), "title": title, "properties": props_schema})


# ---------------------------------------------------------------------------
# Block helpers
# ---------------------------------------------------------------------------

def _flatten_block(block: dict) -> dict:
    btype = block.get("type", "")
    content = block.get(btype, {})
    rich_text = content.get("rich_text", [])
    text = "".join(seg.get("plain_text", "") for seg in rich_text) if rich_text else None

    result: dict = {
        "id": block.get("id", ""),
        "type": btype,
        "has_children": block.get("has_children", False),
    }
    if text is not None:
        result["text"] = text

    if btype == "to_do":
        result["checked"] = content.get("checked", False)
    elif btype in ("image", "file", "pdf", "video"):
        file_obj = content.get("file") or content.get("external") or {}
        result["url"] = file_obj.get("url", "")
    elif btype == "bookmark":
        result["url"] = content.get("url", "")
    elif btype == "code":
        result["language"] = content.get("language", "")

    return result


# ---------------------------------------------------------------------------
# notion block list
# ---------------------------------------------------------------------------

@block_app.command("list")
def block_list(
    block_id: Annotated[str, typer.Argument(help="Block or page UUID")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 100,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """List child blocks."""
    try:
        validate_notion_id(block_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    client = get_client()
    results = []
    cursor: str | None = None
    collected = 0

    while collected < limit:
        kwargs: dict = {"block_id": block_id, "page_size": min(limit - collected, 100)}
        if cursor:
            kwargs["start_cursor"] = cursor
        try:
            response = client.blocks.children.list(**kwargs)
        except APIResponseError as exc:
            _handle_api_error(exc)
        for block in response.get("results", []):
            results.append(_flatten_block(block))
            collected += 1
            if collected >= limit:
                break
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    output(apply_fields(results, fields))


# ---------------------------------------------------------------------------
# notion block get
# ---------------------------------------------------------------------------

@block_app.command("get")
def block_get(
    block_id: Annotated[str, typer.Argument(help="Block UUID")],
) -> None:
    """Retrieve a single block."""
    try:
        validate_notion_id(block_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    client = get_client()
    try:
        block = client.blocks.retrieve(block_id=block_id)
    except APIResponseError as exc:
        _handle_api_error(exc)
    output(_flatten_block(block))


# ---------------------------------------------------------------------------
# notion block append
# ---------------------------------------------------------------------------

@block_app.command("append")
def block_append(
    block_id: Annotated[str, typer.Argument(help="Block or page UUID")],
    body: Annotated[Optional[str], typer.Option("--body", "-b", help="Text to append")] = None,
    blocks_json: Annotated[Optional[str], typer.Option("--blocks-json", help="Block array JSON")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
) -> None:
    """Append child blocks."""
    if not body and not blocks_json:
        output_error("MISSING_PARAM", "--body or --blocks-json required")
        raise typer.Exit(code=1)

    try:
        validate_notion_id(block_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    children: list[dict]
    if blocks_json:
        try:
            children = validate_json_input(blocks_json)
        except ValidationError as exc:
            _handle_validation_error(exc)
    else:
        children = _build_paragraphs(body)

    if dry_run:
        output({"dryRun": True, "action": "blocks.children.append", "block_id": block_id, "children_count": len(children), "children": children})
        return

    client = get_client()
    try:
        response = client.blocks.children.append(block_id=block_id, children=children)
    except APIResponseError as exc:
        _handle_api_error(exc)
    output([_flatten_block(b) for b in response.get("results", [])])


# ---------------------------------------------------------------------------
# notion block delete
# ---------------------------------------------------------------------------

@block_app.command("delete")
def block_delete(
    block_id: Annotated[str, typer.Argument(help="Block UUID")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
) -> None:
    """Delete a block."""
    try:
        validate_notion_id(block_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    if dry_run:
        output({"dryRun": True, "action": "blocks.delete", "block_id": block_id})
        return

    client = get_client()
    try:
        block = client.blocks.delete(block_id=block_id)
    except APIResponseError as exc:
        _handle_api_error(exc)
    output({"id": block.get("id", ""), "archived": block.get("archived", True)})


# ---------------------------------------------------------------------------
# notion comment list
# ---------------------------------------------------------------------------

@comment_app.command("list")
def comment_list(
    block_id: Annotated[str, typer.Argument(help="Page or block UUID")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 100,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """List comments on a page or block."""
    try:
        validate_notion_id(block_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    client = get_client()
    results = []
    cursor: str | None = None
    collected = 0

    while collected < limit:
        kwargs: dict = {"block_id": block_id, "page_size": min(limit - collected, 100)}
        if cursor:
            kwargs["start_cursor"] = cursor
        try:
            response = client.comments.list(**kwargs)
        except APIResponseError as exc:
            _handle_api_error(exc)
        for comment in response.get("results", []):
            rich_text = comment.get("rich_text", [])
            text = "".join(seg.get("plain_text", "") for seg in rich_text)
            results.append({
                "id": comment.get("id", ""),
                "text": text,
                "created_by": comment.get("created_by", {}).get("id", ""),
                "created_time": comment.get("created_time", ""),
            })
            collected += 1
            if collected >= limit:
                break
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    output(apply_fields(results, fields))


# ---------------------------------------------------------------------------
# notion comment create
# ---------------------------------------------------------------------------

@comment_app.command("create")
def comment_create(
    page_id: Annotated[str, typer.Option("--page-id", help="Page UUID")],
    body: Annotated[str, typer.Option("--body", "-b", help="Comment text")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
) -> None:
    """Create a comment on a page."""
    try:
        validate_notion_id(page_id)
    except ValidationError as exc:
        _handle_validation_error(exc)

    if dry_run:
        output({"dryRun": True, "action": "comments.create", "parent": {"page_id": page_id}, "body": body})
        return

    client = get_client()
    try:
        comment = client.comments.create(
            parent={"page_id": page_id},
            rich_text=[{"type": "text", "text": {"content": body}}],
        )
    except APIResponseError as exc:
        _handle_api_error(exc)
    output({"id": comment.get("id", ""), "created_time": comment.get("created_time", "")})


# ---------------------------------------------------------------------------
# notion user list / me
# ---------------------------------------------------------------------------

@user_app.command("list")
def user_list(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 100,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Comma-separated output fields")] = None,
) -> None:
    """List workspace users."""
    client = get_client()
    try:
        response = client.users.list(page_size=min(limit, 100))
    except APIResponseError as exc:
        _handle_api_error(exc)

    results = []
    for user in response.get("results", [])[:limit]:
        results.append({
            "id": user.get("id", ""),
            "type": user.get("type", ""),
            "name": user.get("name", ""),
            "avatar_url": user.get("avatar_url"),
        })
    output(apply_fields(results, fields))


@user_app.command("me")
def user_me() -> None:
    """Get current integration (bot) user info."""
    client = get_client()
    try:
        me = client.users.me()
    except APIResponseError as exc:
        _handle_api_error(exc)
    output({
        "id": me.get("id", ""),
        "type": me.get("type", ""),
        "name": me.get("name", ""),
        "avatar_url": me.get("avatar_url"),
        "bot": me.get("bot", {}),
    })


if __name__ == "__main__":
    app()
