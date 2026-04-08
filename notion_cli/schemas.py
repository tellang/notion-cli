"""Runtime schema introspection — prevents agent hallucination of parameters."""

from __future__ import annotations

SCHEMAS: dict = {
    "search": {
        "command": "search",
        "description": "Search workspace for pages and databases",
        "parameters": {
            "query": {"type": "string", "required": True, "description": "Search keyword"},
            "--type": {"type": "string", "enum": ["page", "db"], "description": "Filter by object type"},
            "--limit": {"type": "integer", "default": 20, "description": "Max results"},
            "--fields": {"type": "string", "description": "Comma-separated fields to return"},
        },
        "response": {
            "type": "array",
            "items": {"type": "object", "properties": {"id": "string", "object": "string", "title": "string", "url": "string"}},
        },
    },
    "page get": {
        "command": "page get",
        "description": "Retrieve page properties as JSON",
        "parameters": {
            "page_id": {"type": "string", "required": True, "description": "Page UUID"},
            "--props": {"type": "string", "description": "Comma-separated property names"},
            "--fields": {"type": "string", "description": "Comma-separated fields to return"},
        },
    },
    "page create": {
        "command": "page create",
        "description": "Create a new page",
        "parameters": {
            "--title": {"type": "string", "required": True, "description": "Page title"},
            "--parent-page": {"type": "string", "description": "Parent page UUID"},
            "--parent-db": {"type": "string", "description": "Parent database UUID"},
            "--body": {"type": "string", "description": "Body text (split into paragraphs)"},
            "--props-json": {"type": "string", "description": "Additional properties JSON"},
            "--dry-run": {"type": "boolean", "default": False, "description": "Preview without executing"},
            "--fields": {"type": "string", "description": "Comma-separated fields to return"},
        },
    },
    "page update": {
        "command": "page update",
        "description": "Update page properties",
        "parameters": {
            "page_id": {"type": "string", "required": True, "description": "Page UUID"},
            "--props-json": {"type": "string", "description": "Properties JSON"},
            "--archive": {"type": "boolean", "description": "Archive the page"},
            "--trash": {"type": "boolean", "description": "Move to trash"},
            "--dry-run": {"type": "boolean", "default": False, "description": "Preview without executing"},
            "--fields": {"type": "string", "description": "Comma-separated fields to return"},
        },
    },
    "db query": {
        "command": "db query",
        "description": "Query a database and return results as JSON",
        "parameters": {
            "database_id": {"type": "string", "required": True, "description": "Database or data_source UUID"},
            "--filter": {"type": "string", "description": "Filter JSON string"},
            "--sort": {"type": "string", "description": "Sort (property:direction)"},
            "--limit": {"type": "integer", "default": 100, "description": "Max results"},
            "--props": {"type": "string", "description": "Comma-separated property names"},
            "--fields": {"type": "string", "description": "Comma-separated fields to return"},
        },
    },
    "db schema": {
        "command": "db schema",
        "description": "Retrieve database schema (property definitions)",
        "parameters": {
            "database_id": {"type": "string", "required": True, "description": "Database or data_source UUID"},
        },
    },
    "block list": {
        "command": "block list",
        "description": "List child blocks of a block or page",
        "parameters": {
            "block_id": {"type": "string", "required": True, "description": "Block or page UUID"},
            "--limit": {"type": "integer", "default": 100, "description": "Max results"},
            "--fields": {"type": "string", "description": "Comma-separated fields to return"},
        },
    },
    "block get": {
        "command": "block get",
        "description": "Retrieve a single block",
        "parameters": {
            "block_id": {"type": "string", "required": True, "description": "Block UUID"},
        },
    },
    "block append": {
        "command": "block append",
        "description": "Append child blocks to a block or page",
        "parameters": {
            "block_id": {"type": "string", "required": True, "description": "Block or page UUID"},
            "--body": {"type": "string", "description": "Text to append (split into paragraphs)"},
            "--blocks-json": {"type": "string", "description": "Block array JSON"},
            "--dry-run": {"type": "boolean", "default": False, "description": "Preview without executing"},
        },
    },
    "block delete": {
        "command": "block delete",
        "description": "Delete a block",
        "parameters": {
            "block_id": {"type": "string", "required": True, "description": "Block UUID"},
            "--dry-run": {"type": "boolean", "default": False, "description": "Preview without executing"},
        },
    },
    "comment list": {
        "command": "comment list",
        "description": "List comments on a page or block",
        "parameters": {
            "block_id": {"type": "string", "required": True, "description": "Page or block UUID"},
            "--limit": {"type": "integer", "default": 100, "description": "Max results"},
        },
    },
    "comment create": {
        "command": "comment create",
        "description": "Create a comment on a page",
        "parameters": {
            "--page-id": {"type": "string", "required": True, "description": "Page UUID"},
            "--body": {"type": "string", "required": True, "description": "Comment text"},
            "--dry-run": {"type": "boolean", "default": False, "description": "Preview without executing"},
        },
    },
    "user list": {
        "command": "user list",
        "description": "List workspace users",
        "parameters": {
            "--limit": {"type": "integer", "default": 100, "description": "Max results"},
        },
    },
    "user me": {
        "command": "user me",
        "description": "Get current integration (bot) user info",
        "parameters": {},
    },
}
