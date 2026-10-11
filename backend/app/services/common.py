"""Helpers shared by service modules."""

LIKE_ESCAPE = "\\"


def escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input is matched literally (use escape='\\\\')."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def like_pattern(value: str) -> str:
    """Contains-pattern for a user supplied search term."""
    return f"%{escape_like(value.strip())}%"
