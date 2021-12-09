"""Mixins."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Tuple

from .utils import JsonEncoder

if TYPE_CHECKING:
    from .protocols import ToDictProtocol


class ToJsonMixin:
    """Mixin that adds ``.to_json()`` method.

    Requires ``.to_dict()`` method.

    """

    def to_json(
        self: ToDictProtocol,
        indent: int = 4,
        sort_keys: bool = True,
        separators: Tuple[str, str] = (",", ": "),
    ):
        """Output object as JSON."""
        return json.dumps(
            self.to_dict(),
            cls=JsonEncoder,
            indent=indent,
            sort_keys=sort_keys,
            separators=separators,
        )
