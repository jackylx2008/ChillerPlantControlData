from __future__ import annotations

from chiller_plant_control_data.context import AppContext
from chiller_plant_control_data.logging_config import get_logger
from chiller_plant_control_data.modules.csv_reader import read_csv_records, write_csv_records
from chiller_plant_control_data.modules.data_cleaner import clean_records
from chiller_plant_control_data.modules.field_mapper import normalize_record_keys


def run(context: AppContext) -> dict[str, object]:
    logger = get_logger(__name__)
    input_path = context.project_root / context.app_config["input_path"]
    output_path = context.output_dir / "cleaned" / f"{input_path.stem}_cleaned.csv"

    logger.info("Reading raw CSV: %s", input_path)
    records = read_csv_records(input_path)
    normalized = [normalize_record_keys(record) for record in records]
    cleaned = clean_records(normalized, **context.flow_config)
    write_csv_records(output_path, cleaned)

    logger.info("Cleaned rows written: %s", output_path)
    return {
        "input_rows": len(records),
        "output_rows": len(cleaned),
        "output_file": str(output_path),
    }

