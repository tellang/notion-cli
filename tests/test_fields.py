"""Tests for notion_cli.lib.fields."""

from notion_cli.lib.fields import apply_fields


def test_apply_fields_none():
    data = {"a": 1, "b": 2, "c": 3}
    assert apply_fields(data, None) == data


def test_apply_fields_single():
    data = {"id": "1", "name": "test", "extra": "skip"}
    result = apply_fields(data, "name")
    assert result == {"id": "1", "name": "test"}


def test_apply_fields_multiple():
    data = {"id": "1", "name": "test", "score": 5, "extra": "skip"}
    result = apply_fields(data, "name,score")
    assert result == {"id": "1", "name": "test", "score": 5}


def test_apply_fields_list():
    data = [
        {"id": "1", "name": "a", "extra": "x"},
        {"id": "2", "name": "b", "extra": "y"},
    ]
    result = apply_fields(data, "name")
    assert result == [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]


def test_apply_fields_always_keeps_id():
    data = {"id": "1", "name": "test"}
    result = apply_fields(data, "name")
    assert "id" in result
