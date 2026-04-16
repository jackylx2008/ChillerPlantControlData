"""展示导出编排模块。

使用说明:
- 负责组织 CSV 数据的展示预览与导出流程。
- 由 `entries/export_views.py` 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

from chiller_plant_control_data.context import AppContext
from chiller_plant_control_data.logging_config import get_logger
from chiller_plant_control_data.modules.csv_reader import write_csv_records
from chiller_plant_control_data.modules.data_cleaner import clean_records
from chiller_plant_control_data.modules.field_mapper import normalize_record_keys
from chiller_plant_control_data.modules.input_loader import load_records_from_path
from chiller_plant_control_data.modules.presenter import format_table, write_json


def run(context: AppContext) -> dict[str, object]:
    logger = get_logger(__name__)
    input_path = context.input_path
    flow_config = context.entry_flow_config
    source_glob = str(flow_config.get("source_glob", "*.csv"))
    limit = int(flow_config.get("table_limit", 20))

    logger.info("Exporting views from: %s", input_path)
    records, files = load_records_from_path(input_path, pattern=source_glob)
    records = [normalize_record_keys(record) for record in records]
    cleaned = clean_records(records)

    preview_text = format_table(cleaned, limit=limit)
    preview_path = context.output_dir / "views" / "preview.txt"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text(preview_text, encoding="utf-8")

    if "csv" in flow_config.get("export_formats", []):
        write_csv_records(context.output_dir / "views" / "cleaned_view.csv", cleaned)
    if "json" in flow_config.get("export_formats", []):
        write_json(context.output_dir / "views" / "cleaned_view.json", cleaned)

    logger.info("View exports written under: %s", preview_path.parent)
    return {
        "source_files": [str(file_path) for file_path in files],
        "source_file_count": len(files),
        "preview_file": str(preview_path),
        "preview_rows": min(len(cleaned), limit),
    }
