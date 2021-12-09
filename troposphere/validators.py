"""Validator functions."""
from __future__ import annotations

from typing import Any


def validate_delimiter(delimiter: Any) -> None:
    """Validate delimiter is a string."""
    if not isinstance(delimiter, str):
        raise ValueError(f"Delimiter must be a String, {type(delimiter)} provided")
