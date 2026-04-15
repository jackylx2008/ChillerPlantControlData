from __future__ import annotations

from typing import Any


def normalize_field_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def normalize_record_keys(record: dict[str, Any]) -> dict[str, Any]:
    return {normalize_field_name(key): value for key, value in record.items()}

