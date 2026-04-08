"""Tests for notion_cli.lib.validate."""

import pytest

from notion_cli.lib.validate import (
    ValidationError,
    reject_control_chars,
    reject_dangerous_unicode,
    validate_json_input,
    validate_notion_id,
)


def test_reject_control_chars_clean():
    reject_control_chars("hello world")


def test_reject_control_chars_null():
    with pytest.raises(ValidationError):
        reject_control_chars("hello\x00world")


def test_reject_control_chars_tab():
    with pytest.raises(ValidationError):
        reject_control_chars("hello\tworld")


def test_reject_dangerous_unicode_clean():
    reject_dangerous_unicode("normal text 한글")


def test_reject_dangerous_unicode_zwsp():
    with pytest.raises(ValidationError, match="U\\+200B"):
        reject_dangerous_unicode("hello\u200bworld")


def test_reject_dangerous_unicode_rtl():
    with pytest.raises(ValidationError, match="U\\+202E"):
        reject_dangerous_unicode("abc\u202edef")


def test_validate_notion_id_valid_with_dashes():
    result = validate_notion_id("a23867b1-ab41-468c-83df-8435bdbf03f8")
    assert result == "a23867b1-ab41-468c-83df-8435bdbf03f8"


def test_validate_notion_id_valid_no_dashes():
    validate_notion_id("a23867b1ab41468c83df8435bdbf03f8")


def test_validate_notion_id_invalid():
    with pytest.raises(ValidationError, match="Invalid Notion ID"):
        validate_notion_id("not-a-uuid")


def test_validate_notion_id_path_traversal():
    with pytest.raises(ValidationError):
        validate_notion_id("../../etc/passwd")


def test_validate_json_input_valid():
    result = validate_json_input('{"key": "value"}')
    assert result == {"key": "value"}


def test_validate_json_input_invalid():
    with pytest.raises(ValidationError, match="Invalid JSON"):
        validate_json_input("{broken")


def test_validate_json_input_control_chars():
    with pytest.raises(ValidationError):
        validate_json_input('{"key": "val\x00ue"}')
