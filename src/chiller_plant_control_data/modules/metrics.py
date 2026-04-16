"""指标汇总模块。

使用说明:
- 提供数值字段的分组统计能力，如 count、avg、min、max。
- 主要由 `report_flow.py` 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_numeric_fields(records: list[dict[str, Any]], numeric_fields: list[str], group_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for record in records:
        bucket = str(record.get(group_key) or "unknown")
        for field in numeric_fields:
            value = _to_float(record.get(field))
            if value is not None:
                grouped[bucket][field].append(value)

    summaries: list[dict[str, Any]] = []
    for bucket, metrics in sorted(grouped.items()):
        row: dict[str, Any] = {"group": bucket}
        for field in numeric_fields:
            values = metrics.get(field, [])
            row[f"{field}_count"] = len(values)
            row[f"{field}_avg"] = round(mean(values), 3) if values else None
            row[f"{field}_min"] = round(min(values), 3) if values else None
            row[f"{field}_max"] = round(max(values), 3) if values else None
        summaries.append(row)
    return summaries
