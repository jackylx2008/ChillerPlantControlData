"""CSV 读写模块。

使用说明:
- 提供 CSV 表头识别、记录读取和结果写出能力。
- 能处理带前导说明行的趋势报表 CSV。
- 由 `input_loader.py` 和各类 flow 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def _is_strong_header_row(row: list[str]) -> bool:
    cleaned = [cell.strip() for cell in row]
    non_empty = [cell for cell in cleaned if cell]
    if len(non_empty) < 2:
        return False

    first_cell = non_empty[0].lower()
    return first_cell in {"timestamp", "time", "datetime", "date"}


def _is_header_row(row: list[str]) -> bool:
    cleaned = [cell.strip() for cell in row]
    non_empty = [cell for cell in cleaned if cell]
    if len(non_empty) < 2:
        return False

    # Generic fallback for standard CSV exports whose header row is mostly textual.
    text_like = sum(any(char.isalpha() for char in cell) for cell in non_empty)
    numeric_like = sum(cell.replace(".", "", 1).replace("-", "", 1).isdigit() for cell in non_empty)
    return text_like >= 2 and numeric_like == 0


def _sanitize_headers(row: list[str]) -> list[str]:
    headers: list[str] = []
    for index, cell in enumerate(row):
        header = cell.strip()
        headers.append(header if header else f"unnamed_column_{index + 1}")
    return headers


def read_csv_records(file_path: Path | str, encoding: str = "utf-8-sig") -> list[dict[str, Any]]:
    path = Path(file_path)
    with path.open("r", encoding=encoding, newline="") as handle:
        rows = list(csv.reader(handle))

    header_index = next((index for index, row in enumerate(rows) if _is_strong_header_row(row)), None)
    if header_index is None:
        header_index = next((index for index, row in enumerate(rows) if _is_header_row(row)), None)
    if header_index is None:
        raise ValueError(f"Could not identify a header row in CSV: {path}")

    headers = _sanitize_headers(rows[header_index])
    records: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        if not any(cell.strip() for cell in row):
            continue

        padded_row = list(row[: len(headers)])
        if len(padded_row) < len(headers):
            padded_row.extend("" for _ in range(len(headers) - len(padded_row)))

        records.append({headers[index]: padded_row[index] for index in range(len(headers))})

    return records


def write_csv_records(file_path: Path | str, rows: list[dict[str, Any]]) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
