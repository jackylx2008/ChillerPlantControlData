"""报表生成编排模块。

使用说明:
- 负责组织 CSV 数据汇总、分组统计和报表写出流程。
- 由 `entries/generate_report.py` 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

from chiller_plant_control_data.context import AppContext
from chiller_plant_control_data.logging_config import get_logger
from chiller_plant_control_data.modules.csv_reader import write_csv_records
from chiller_plant_control_data.modules.data_cleaner import clean_records
from chiller_plant_control_data.modules.field_mapper import normalize_record_keys
from chiller_plant_control_data.modules.input_loader import load_records_from_path
from chiller_plant_control_data.modules.metrics import summarize_numeric_fields
from chiller_plant_control_data.modules.presenter import write_json
from chiller_plant_control_data.modules.time_parser import attach_timestamp


def run(context: AppContext) -> dict[str, object]:
    logger = get_logger(__name__)
    input_path = context.input_path
    flow_config = context.entry_flow_config
    source_glob = str(flow_config.get("source_glob", "*.csv"))

    logger.info("Preparing report from: %s", input_path)
    records, files = load_records_from_path(input_path, pattern=source_glob)
    records = [normalize_record_keys(record) for record in records]
    cleaned = clean_records(records)
    enriched = [attach_timestamp(record, field_name=flow_config.get("time_field", "timestamp")) for record in cleaned]

    for row in enriched:
        parsed = row.get("_parsed_timestamp")
        row["day"] = parsed.strftime("%Y-%m-%d") if parsed else "unknown"
        row["hour"] = parsed.strftime("%Y-%m-%d %H:00") if parsed else "unknown"

    group_by = flow_config.get("group_by", "day")
    summary = summarize_numeric_fields(enriched, flow_config.get("numeric_fields", []), group_by)

    csv_path = context.output_dir / "reports" / f"{group_by}_summary.csv"
    json_path = context.output_dir / "reports" / f"{group_by}_summary.json"
    write_csv_records(csv_path, summary)
    write_json(json_path, summary)

    logger.info("Report files written: %s, %s", csv_path, json_path)
    return {
        "source_files": [str(file_path) for file_path in files],
        "source_file_count": len(files),
        "group_by": group_by,
        "summary_rows": len(summary),
        "csv_file": str(csv_path),
        "json_file": str(json_path),
    }
