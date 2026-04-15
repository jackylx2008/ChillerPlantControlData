from __future__ import annotations

from datetime import datetime
from typing import Any


TIME_PATTERNS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    text = value.strip()
    for pattern in TIME_PATTERNS:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def attach_timestamp(record: dict[str, Any], field_name: str = "timestamp") -> dict[str, Any]:
    enriched = dict(record)
    enriched["_parsed_timestamp"] = parse_timestamp(str(record.get(field_name, "")).strip())
    return enriched

