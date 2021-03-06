"""Validator functions."""
from __future__ import annotations

from typing import Any


def validate_delimiter(delimiter: Any) -> str:
    """Validate delimiter is a string."""
    if not isinstance(delimiter, str):
        raise ValueError(f"Delimiter must be a String, {type(delimiter)} provided")
    return delimiter


def validate_pause_time(pause_time: str) -> str:
    """Validate pause time."""
    if not pause_time.startswith("PT"):
        raise ValueError("PauseTime should look like PT#H#M#S")
    return pause_time
