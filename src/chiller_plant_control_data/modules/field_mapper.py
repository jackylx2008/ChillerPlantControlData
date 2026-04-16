"""字段名标准化模块。

使用说明:
- 负责把原始字段名统一成更稳定的内部字段格式。
- 会处理空字段名并生成兜底名称。
- 由清洗、报表、展示等 flow 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

from typing import Any


def normalize_field_name(name: Any) -> str:
    text = "" if name is None else str(name)
    normalized = text.strip().lower().replace(" ", "_").replace("-", "_")
    return normalized or "unnamed_column"


def normalize_record_keys(record: dict[str, Any]) -> dict[str, Any]:
    return {normalize_field_name(key): value for key, value in record.items()}
