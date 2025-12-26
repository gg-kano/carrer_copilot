"""
Tests for text utility functions
"""

import pytest
from utils.text_utils import (
    normalize_text,
    clean_name_for_id,
    truncate_text,
    extract_json_from_text,
    format_list_as_string
)


class TestNormalizeText:
    """Test text normalization function"""

    def test_remove_html_tags(self):
        """Test HTML tag removal"""
        text = "<p>Hello <strong>World</strong></p>"
        result = normalize_text(text)
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "Hello World" in result

    def test_replace_urls(self):
        """Test URL replacement"""
        text = "Visit https://example.com for more info"
        result = normalize_text(text)
        assert "https://example.com" not in result
        assert "[URL]" in result

    def test_normalize_whitespace(self):
        """Test whitespace normalization"""
        text = "Hello    World\n\nTest"
        result = normalize_text(text)
        assert "  " not in result  # No double spaces
        assert result == "Hello World Test"

    def test_empty_string(self):
        """Test empty string handling"""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestCleanNameForId:
    """Test name cleaning for ID generation"""

    def test_simple_name(self):
        """Test cleaning a simple name"""
        result = clean_name_for_id("John Doe")
        assert result == "john_doe"

    def test_special_characters(self):
        """Test removal of special characters"""
        result = clean_name_for_id("María García-López")
        assert "_" in result
        assert "-" not in result

    def test_unknown_name(self):
        """Test handling of unknown names"""
        assert clean_name_for_id("Unknown") is None
        assert clean_name_for_id("unknown") is None

    def test_empty_name(self):
        """Test empty name handling"""
        assert clean_name_for_id("") is None
        assert clean_name_for_id(None) is None


class TestTruncateText:
    """Test text truncation"""

    def test_truncate_long_text(self):
        """Test truncating text longer than max_length"""
        text = "Hello World"
        result = truncate_text(text, max_length=8)
        assert len(result) == 8
        assert result.endswith("...")

    def test_short_text_unchanged(self):
        """Test that short text is not truncated"""
        text = "Short"
        result = truncate_text(text, max_length=10)
        assert result == "Short"

    def test_custom_suffix(self):
        """Test custom suffix"""
        text = "Hello World"
        result = truncate_text(text, max_length=8, suffix=">>")
        assert result.endswith(">>")


class TestExtractJsonFromText:
    """Test JSON extraction"""

    def test_extract_json_with_markdown(self):
        """Test extracting JSON from markdown code block"""
        text = '```json\n{"key": "value"}\n```'
        result = extract_json_from_text(text)
        assert result == '{"key": "value"}'

    def test_extract_json_from_mixed_text(self):
        """Test extracting JSON from mixed content"""
        text = 'Some text {"key": "value"} more text'
        result = extract_json_from_text(text)
        assert '"key"' in result
        assert '"value"' in result

    def test_no_json_found(self):
        """Test handling of text without JSON"""
        text = "No JSON here"
        result = extract_json_from_text(text)
        assert result is None


class TestFormatListAsString:
    """Test list formatting"""

    def test_simple_list(self):
        """Test formatting a simple list"""
        items = ['a', 'b', 'c']
        result = format_list_as_string(items)
        assert result == "a, b, c"

    def test_list_with_max_items(self):
        """Test list truncation with max_items"""
        items = ['a', 'b', 'c', 'd']
        result = format_list_as_string(items, max_items=2)
        assert "a" in result
        assert "b" in result
        assert "+2 more" in result

    def test_empty_list(self):
        """Test empty list handling"""
        assert format_list_as_string([]) == ""

    def test_custom_separator(self):
        """Test custom separator"""
        items = ['x', 'y']
        result = format_list_as_string(items, separator=" | ")
        assert result == "x | y"
