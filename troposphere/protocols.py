"""Protocols."""
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Protocol


class ToDictProtocol(Protocol):
    """Class with a ``.to_dict`` method."""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError
