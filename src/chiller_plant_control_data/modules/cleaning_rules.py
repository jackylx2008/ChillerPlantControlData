"""清洗规则模块。

使用说明:
- 提供清洗输出文件命名、时间列格式化、空列删除、数据源列补充等规则函数。
- 主要由 `flows/clean_data_flow.py` 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from chiller_plant_control_data.modules.time_parser import format_timestamp_text


_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
_TIME_FIELD_PATTERN = re.compile(r"(timestamp|time|date|datetime)", re.IGNORECASE)


def build_cleaned_filename(source_file: Path | str) -> str:
    path = Path(source_file)
    chinese_parts = _CHINESE_PATTERN.findall(path.stem)
    if chinese_parts:
        label = "_".join(chinese_parts)
    else:
        label = path.stem.replace(" ", "_")
    return f"cleaned_{label}.csv"


def attach_source_column(records: list[dict[str, Any]], source_name: str) -> list[dict[str, Any]]:
    return [{**row, "数据源": source_name} for row in records]


def drop_empty_columns(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return records

    kept_keys = [
        key
        for key in records[0].keys()
        if key == "数据源" or any(row.get(key) not in (None, "") for row in records)
    ]
    return [{key: row.get(key) for key in kept_keys} for row in records]


def normalize_timestamp_columns(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_rows: list[dict[str, Any]] = []
    for row in records:
        normalized_row: dict[str, Any] = {}
        for key, value in row.items():
            if _TIME_FIELD_PATTERN.search(key):
                normalized_row[key] = format_timestamp_text(value)
            else:
                normalized_row[key] = value
        normalized_rows.append(normalized_row)
    return normalized_rows
