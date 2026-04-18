"""数据清洗基础模块。

使用说明:
- 提供通用的数据值清洗、空行删除、异常状态过滤和重复数据去除能力。
- 由 `clean_data_flow.py`、`report_flow.py`、`export_views_flow.py` 调用。
- 不直接运行本文件。
"""

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

        if any(str(value).strip() == "Bad Status" for value in cleaned.values() if value is not None):
            continue

        if drop_empty_rows and all(value in (None, "") for value in cleaned.values()):
            continue

        if deduplicate:
            fingerprint = tuple(sorted(cleaned.items()))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)

        cleaned_rows.append(cleaned)

    return cleaned_rows
