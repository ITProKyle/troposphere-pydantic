"""Utilities."""
from __future__ import annotations

import datetime
import json
from decimal import Decimal
from typing import Any


class JsonEncoder(json.JSONEncoder):
    """Encode Python objects to JSON data.

    This class can be used with ``json.dumps()`` to handle most data types
    that can occur in responses from AWS.

    Usage:
        >>> json.dumps(data, cls=JsonEncoder)

    """

    def default(self, o: object) -> Any:
        """Encode types not supported by the default JSONEncoder.

        Args:
            o: Object to encode.

        Returns:
            JSON serializable data type.

        Raises:
            TypeError: Object type could not be encoded.

        """
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        if hasattr(o, "to_dict"):
            return o.to_dict()  # type: ignore
        return super().default(o)
