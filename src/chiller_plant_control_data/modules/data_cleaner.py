from __future__ import annotations

from typing import Any


def _clean_value(value: Any, trim_whitespace: bool = True) -> Any:
    if isinstance(value, str):
        cleaned = value.strip() if trim_whitespace else value
        return cleaned if cleaned != "" else None
    return value


def clean_records(
    records: list[dict[str, Any]],
    *,
    trim_whitespace: bool = True,
    drop_empty_rows: bool = True,
    deduplicate: bool = True,
) -> list[dict[str, Any]]:
    cleaned_rows: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, Any], ...]] = set()

    for record in records:
        cleaned = {key: _clean_value(value, trim_whitespace=trim_whitespace) for key, value in record.items()}

        if drop_empty_rows and all(value in (None, "") for value in cleaned.values()):
            continue

        if deduplicate:
            fingerprint = tuple(sorted(cleaned.items()))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)

        cleaned_rows.append(cleaned)

    return cleaned_rows

