"""输入源加载模块。

使用说明:
- 负责解析 `INPUT_PATH`，支持传入单个 CSV 文件或目录。
- 如果输入是目录，会按给定 `glob` 规则扫描 CSV 文件。
- 由各类 flow 调用，不直接运行本文件。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chiller_plant_control_data.modules.csv_reader import read_csv_records


def resolve_csv_files(input_path: Path | str, pattern: str = "*.csv") -> list[Path]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")
    if path.is_file():
        return [path]
    return sorted(file_path for file_path in path.glob(pattern) if file_path.is_file())


def load_records_from_path(input_path: Path | str, pattern: str = "*.csv") -> tuple[list[dict[str, Any]], list[Path]]:
    files = resolve_csv_files(input_path, pattern=pattern)
    all_records: list[dict[str, Any]] = []

    for file_path in files:
        for row in read_csv_records(file_path):
            enriched = dict(row)
            enriched["_source_file"] = file_path.name
            all_records.append(enriched)

    return all_records, files
