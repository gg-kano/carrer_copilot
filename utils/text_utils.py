"""
Text Processing Utilities

Shared text processing functions used across the application.
"""

import re
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text by removing HTML tags, URLs, and extra whitespace.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text string

    Examples:
        >>> normalize_text("<p>Hello  World</p>")
        'Hello World'
        >>> normalize_text("Visit https://example.com for more")
        'Visit [URL] for more'
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Replace URLs with placeholder
    text = re.sub(r'http[s]?://\S+', '[URL]', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def clean_name_for_id(name: str) -> Optional[str]:
    """
    Clean a person's name to create a valid ID.

    Removes special characters, converts to lowercase, and replaces
    spaces with underscores.

    Args:
        name: Person's name

    Returns:
        Cleaned name suitable for use as an ID, or None if name is invalid

    Examples:
        >>> clean_name_for_id("John Doe")
        'john_doe'
        >>> clean_name_for_id("María García-López")
        'mara_garca_lpez'
        >>> clean_name_for_id("Unknown")
        None
    """
    if not name or name.lower() == "unknown":
        return None

    # Remove special characters except spaces and hyphens
    clean_name = re.sub(r'[^\w\s-]', '', name)

    # Replace spaces with underscores
    clean_name = re.sub(r'\s+', '_', clean_name.strip())

    # Convert to lowercase
    clean_name = clean_name.lower()

    # Return None if empty after cleaning
    return clean_name if clean_name else None


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with a suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length of the truncated text (including suffix)
        suffix: String to append when text is truncated

    Returns:
        Truncated text

    Examples:
        >>> truncate_text("Hello World", max_length=8)
        'Hello...'
        >>> truncate_text("Short", max_length=10)
        'Short'
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Account for suffix length
    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON object from text that may contain markdown or other content.

    Args:
        text: Text that may contain JSON

    Returns:
        Extracted JSON string, or None if no JSON found

    Examples:
        >>> extract_json_from_text('```json\\n{"key": "value"}\\n```')
        '{"key": "value"}'
        >>> extract_json_from_text('Some text {"key": "value"} more text')
        '{"key": "value"}'
    """
    if not text:
        return None

    # Remove markdown code blocks
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())

    # Try to extract JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group() if match else None


def format_list_as_string(
    items: list,
    max_items: Optional[int] = None,
    separator: str = ", ",
    overflow_suffix: str = " ... (+{count} more)"
) -> str:
    """
    Format a list as a human-readable string.

    Args:
        items: List of items to format
        max_items: Maximum number of items to display
        separator: String to use between items
        overflow_suffix: Suffix to show when items are truncated

    Returns:
        Formatted string

    Examples:
        >>> format_list_as_string(['a', 'b', 'c'], max_items=2)
        'a, b ... (+1 more)'
        >>> format_list_as_string(['x', 'y'])
        'x, y'
    """
    if not items:
        return ""

    if max_items and len(items) > max_items:
        displayed_items = items[:max_items]
        overflow_count = len(items) - max_items
        suffix = overflow_suffix.format(count=overflow_count)
        return separator.join(str(item) for item in displayed_items) + suffix

    return separator.join(str(item) for item in items)
