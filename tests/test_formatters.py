"""Tests for notion_cli.formatters."""

from notion_cli.formatters import (
    extract_multi_select,
    extract_property_value,
    extract_rich_text,
    extract_select,
    extract_title,
    flatten_page,
)


def test_extract_title():
    prop = {"title": [{"plain_text": "Hello"}, {"plain_text": " World"}]}
    assert extract_title(prop) == "Hello World"


def test_extract_title_empty():
    assert extract_title({}) == ""


def test_extract_rich_text():
    prop = {"rich_text": [{"plain_text": "some text"}]}
    assert extract_rich_text(prop) == "some text"


def test_extract_select():
    assert extract_select({"select": {"name": "Option A"}}) == "Option A"
    assert extract_select({"select": None}) is None
    assert extract_select({}) is None


def test_extract_multi_select():
    prop = {"multi_select": [{"name": "A"}, {"name": "B"}]}
    assert extract_multi_select(prop) == ["A", "B"]
    assert extract_multi_select({}) == []


def test_extract_property_value_number():
    prop = {"type": "number", "number": 42}
    assert extract_property_value(prop) == 42


def test_extract_property_value_checkbox():
    prop = {"type": "checkbox", "checkbox": True}
    assert extract_property_value(prop) is True


def test_extract_property_value_url():
    prop = {"type": "url", "url": "https://example.com"}
    assert extract_property_value(prop) == "https://example.com"


def test_extract_property_value_date():
    prop = {"type": "date", "date": {"start": "2026-04-08", "end": None}}
    assert extract_property_value(prop) == {"start": "2026-04-08", "end": None}


def test_extract_property_value_unique_id():
    prop = {"type": "unique_id", "unique_id": {"prefix": "PRJ", "number": 42}}
    assert extract_property_value(prop) == "PRJ-42"


def test_extract_property_value_status():
    prop = {"type": "status", "status": {"name": "Done"}}
    assert extract_property_value(prop) == "Done"


def test_flatten_page():
    page = {
        "id": "abc-123",
        "url": "https://notion.so/abc",
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": "Test"}]},
            "Score": {"type": "number", "number": 8.5},
            "Tags": {"type": "multi_select", "multi_select": [{"name": "A"}]},
        },
    }
    result = flatten_page(page)
    assert result["id"] == "abc-123"
    assert result["Name"] == "Test"
    assert result["Score"] == 8.5
    assert result["Tags"] == ["A"]


def test_flatten_page_with_filter():
    page = {
        "id": "abc-123",
        "url": "https://notion.so/abc",
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": "Test"}]},
            "Score": {"type": "number", "number": 8.5},
            "Extra": {"type": "rich_text", "rich_text": [{"plain_text": "skip"}]},
        },
    }
    result = flatten_page(page, props_filter=["Name", "Score"])
    assert "Name" in result
    assert "Score" in result
    assert "Extra" not in result
