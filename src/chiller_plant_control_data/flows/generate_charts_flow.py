"""图表生成编排模块。

使用说明:
- 负责从清洗后的 CSV 文件中按关键词匹配目标文件。
- 支持按某一天或某一个月筛选数据并生成图表。
- 由 `entries/generate_charts.py` 调用。
- 不直接运行本文件。
"""

from __future__ import annotations

from pathlib import Path

from chiller_plant_control_data.context import AppContext
from chiller_plant_control_data.logging_config import get_logger
from chiller_plant_control_data.modules.charting import (
    attach_chart_timestamp,
    build_chart_display_label,
    build_chart_output_name,
    detect_numeric_fields,
    filter_records_by_period,
    find_cleaned_files,
    plot_missing_data_placeholder,
    plot_time_series_chart,
)
from chiller_plant_control_data.modules.csv_reader import read_csv_records


def _merge_records_for_chart(
    file_records: list[tuple[Path, list[dict[str, object]]]],
    field_labels: dict[str, str],
) -> tuple[list[dict[str, object]], list[str]]:
    merged_rows_by_timestamp: dict[object, dict[str, object]] = {}
    merged_numeric_fields: list[str] = []
    combine_as_single_series = len(file_records) > 1

    for file_path, records in file_records:
        file_label = build_chart_display_label("", [file_path])
        numeric_fields = detect_numeric_fields(records)
        if not numeric_fields:
            continue

        for row in records:
            timestamp = row.get("_chart_timestamp")
            if timestamp is None:
                continue
            merged_row = merged_rows_by_timestamp.setdefault(
                timestamp,
                {
                    "_chart_timestamp": timestamp,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

            if combine_as_single_series:
                value_field = numeric_fields[0]
                if file_label not in merged_numeric_fields:
                    merged_numeric_fields.append(file_label)
                field_labels.setdefault(file_label, file_label)
                merged_row[file_label] = row.get(value_field)
                continue

            for numeric_field in numeric_fields:
                if numeric_field not in merged_numeric_fields:
                    merged_numeric_fields.append(numeric_field)
                merged_row[numeric_field] = row.get(numeric_field)

    merged_rows = [merged_rows_by_timestamp[key] for key in sorted(merged_rows_by_timestamp)]
    return merged_rows, merged_numeric_fields


def _resolve_expected_numeric_fields(
    file_records: list[tuple[Path, list[dict[str, object]]]],
    field_labels: dict[str, str],
) -> list[str]:
    expected_fields: list[str] = []
    combine_as_single_series = len(file_records) > 1

    for file_path, records in file_records:
        numeric_fields = detect_numeric_fields(records)
        if not numeric_fields:
            continue

        if combine_as_single_series:
            file_label = build_chart_display_label("", [file_path])
            if file_label not in expected_fields:
                expected_fields.append(file_label)
            field_labels.setdefault(file_label, file_label)
            continue

        for numeric_field in numeric_fields:
            if numeric_field not in expected_fields:
                expected_fields.append(numeric_field)

    return expected_fields


def run(context: AppContext) -> dict[str, object]:
    logger = get_logger(__name__)
    flow_config = context.entry_flow_config
    metadata = context.metadata
    cleaned_dir = context.project_root / str(metadata.get("cleaned_dir") or flow_config.get("cleaned_dir", "output/cleaned"))
    keyword = str(metadata.get("keyword") or flow_config.get("keyword", "")).strip()
    file_glob = str(metadata.get("file_glob") or flow_config.get("file_glob", "cleaned_*.csv"))
    period_type = str(metadata.get("period_type") or flow_config.get("period_type", "day")).strip().lower()
    target_date = str(metadata.get("target_date") or flow_config.get("target_date", "")).strip()
    target_month = str(metadata.get("target_month") or flow_config.get("target_month", "")).strip()
    timestamp_field = str(metadata.get("timestamp_field") or flow_config.get("timestamp_field", "timestamp")).strip()
    field_labels = dict(flow_config.get("field_labels", {}))

    if period_type not in {"day", "month"}:
        raise ValueError(f"Unsupported period_type: {period_type}")

    target_label = target_date if period_type == "day" else target_month
    chart_dir = context.output_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    files = find_cleaned_files(cleaned_dir, keyword=keyword, file_glob=file_glob)
    logger.info("Generating charts from cleaned dir: %s", cleaned_dir)
    chart_label = build_chart_display_label(keyword, files)

    outputs: list[dict[str, object]] = []
    filtered_groups: list[tuple[Path, list[dict[str, object]]]] = []
    all_groups: list[tuple[Path, list[dict[str, object]]]] = []
    for file_path in files:
        records = read_csv_records(file_path)
        records = attach_chart_timestamp(records, timestamp_field=timestamp_field)
        all_groups.append((file_path, records))
        filtered = filter_records_by_period(
            records,
            period_type=period_type,
            target_date=target_date,
            target_month=target_month,
        )
        numeric_fields = detect_numeric_fields(filtered)
        if not filtered or not numeric_fields:
            outputs.append(
                {
                    "source_file": str(file_path),
                    "matched_rows": len(filtered),
                    "chart_file": None,
                    "numeric_fields": numeric_fields,
                }
            )
            continue
        filtered_groups.append((file_path, filtered))

    if filtered_groups:
        plot_records, plot_fields = _merge_records_for_chart(filtered_groups, field_labels)
        chart_file = chart_dir / build_chart_output_name(chart_label, period_type, target_label)
        plot_time_series_chart(
            plot_records,
            numeric_fields=plot_fields,
            title=chart_label,
            output_path=chart_file,
            field_labels=field_labels,
        )
        outputs.append(
            {
                "source_files": [str(file_path) for file_path, _ in filtered_groups],
                "matched_rows": sum(len(records) for _, records in filtered_groups),
                "chart_file": str(chart_file),
                "numeric_fields": plot_fields,
            }
        )
        logger.info("Chart written: %s", chart_file)
    elif period_type == "day":
        expected_fields = _resolve_expected_numeric_fields(all_groups, field_labels)
        chart_file = chart_dir / build_chart_output_name(chart_label, period_type, target_label)
        plot_missing_data_placeholder(
            title=chart_label,
            output_path=chart_file,
            numeric_fields=expected_fields,
            target_label=target_label,
            field_labels=field_labels,
        )
        outputs.append(
            {
                "source_files": [str(file_path) for file_path in files],
                "matched_rows": 0,
                "chart_file": str(chart_file),
                "numeric_fields": expected_fields,
                "placeholder": True,
            }
        )
        logger.info("Missing-data placeholder chart written: %s", chart_file)

    return {
        "keyword": keyword,
        "chart_label": chart_label,
        "period_type": period_type,
        "target_label": target_label,
        "matched_file_count": len(files),
        "chart_dir": str(chart_dir),
        "outputs": outputs,
    }
