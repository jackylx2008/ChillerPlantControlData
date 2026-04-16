"""时间解析模块。

使用说明:
- 提供时间字符串解析、时间字段挂载和统一格式化能力。
- 支持常见数字时间格式和英文月份时间格式。
- 由清洗和报表流程调用，不直接运行本文件。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


TIME_PATTERNS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
    "%B %d, %Y %I:%M:%S %p",
    "%b %d, %Y %I:%M:%S %p",
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


def format_timestamp_text(value: Any, output_pattern: str = "%Y-%m-%d %H:%M:%S") -> Any:
    if value in (None, ""):
        return value

    parsed = parse_timestamp(str(value))
    if parsed is None:
        return value
    return parsed.strftime(output_pattern)
