"""数据清洗编排模块。

使用说明:
- 负责组织单个或多个 CSV 文件的清洗流程。
- 包括读取输入、清理旧输出、字段标准化、时间格式化、空列删除和结果写出。
- 由 `entries/clean_data.py` 调用，不直接运行本文件。
"""

from __future__ import annotations

import shutil

from chiller_plant_control_data.context import AppContext
from chiller_plant_control_data.logging_config import get_logger
from chiller_plant_control_data.modules.cleaning_rules import (
    attach_source_column,
    build_cleaned_filename,
    drop_empty_columns,
    normalize_timestamp_columns,
)
from chiller_plant_control_data.modules.csv_reader import read_csv_records, write_csv_records
from chiller_plant_control_data.modules.data_cleaner import clean_records
from chiller_plant_control_data.modules.field_mapper import normalize_record_keys
from chiller_plant_control_data.modules.input_loader import resolve_csv_files


def run(context: AppContext) -> dict[str, object]:
    logger = get_logger(__name__)
    input_path = context.input_path
    flow_config = context.entry_flow_config
    source_glob = str(flow_config.get("source_glob", "*.csv"))
    cleaned_dir = context.output_dir / "cleaned"
    files = resolve_csv_files(input_path, pattern=source_glob)
    results: list[dict[str, object]] = []
    total_input_rows = 0
    total_output_rows = 0

    if cleaned_dir.exists():
        shutil.rmtree(cleaned_dir)
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Reading raw CSV data from: %s", input_path)
    for file_path in files:
        raw_records = read_csv_records(file_path)
        normalized = [normalize_record_keys(record) for record in raw_records]
        cleaned = clean_records(
            normalized,
            trim_whitespace=bool(flow_config.get("trim_whitespace", True)),
            drop_empty_rows=bool(flow_config.get("drop_empty_rows", True)),
            deduplicate=bool(flow_config.get("deduplicate", True)),
        )
        cleaned = attach_source_column(cleaned, file_path.name)
        cleaned = normalize_timestamp_columns(cleaned)
        cleaned = drop_empty_columns(cleaned)

        output_path = cleaned_dir / build_cleaned_filename(file_path)
        write_csv_records(output_path, cleaned)

        total_input_rows += len(raw_records)
        total_output_rows += len(cleaned)
        results.append(
            {
                "source_file": str(file_path),
                "input_rows": len(raw_records),
                "output_rows": len(cleaned),
                "output_file": str(output_path),
            }
        )
        logger.info("Cleaned rows written: %s", output_path)

    return {
        "source_files": [str(file_path) for file_path in files],
        "source_file_count": len(files),
        "input_rows": total_input_rows,
        "output_rows": total_output_rows,
        "output_dir": str(cleaned_dir),
        "outputs": results,
    }
