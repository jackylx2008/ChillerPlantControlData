"""图表展示模块。

使用说明:
- 提供清洗后 CSV 的匹配、筛选、数值列识别和图表生成能力。
- 主要由 `generate_charts_flow.py` 调用。
- 输出 PNG 图表和筛选后的 CSV 数据。
- 不直接运行本文件。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt

from chiller_plant_control_data.modules.time_parser import parse_timestamp


GAP_BREAK_THRESHOLD = timedelta(hours=1)
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
COMBINED_KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "总供回水温度": ("总供水温度", "总回水温度"),
    "总供回水压力": ("总供水压力", "总回水压力"),
}
KEYWORD_ALIAS_TO_GROUP = {
    alias: canonical
    for canonical, labels in COMBINED_KEYWORD_GROUPS.items()
    for alias in (canonical, *labels)
}


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace(",", "")
    if text == "":
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def find_cleaned_files(cleaned_dir: Path | str, keyword: str, file_glob: str = "cleaned_*.csv") -> list[Path]:
    directory = Path(cleaned_dir)
    candidate_files = [file_path for file_path in sorted(directory.glob(file_glob)) if file_path.is_file()]
    canonical_keyword = KEYWORD_ALIAS_TO_GROUP.get(keyword, keyword)

    if canonical_keyword in COMBINED_KEYWORD_GROUPS:
        target_labels = COMBINED_KEYWORD_GROUPS[canonical_keyword]
        matched = [
            file_path
            for label in target_labels
            for file_path in candidate_files
            if extract_chinese_label(file_path) == label
        ]
        return matched

    return [
        file_path
        for file_path in candidate_files
        if keyword in file_path.stem or keyword == extract_chinese_label(file_path)
    ]


def extract_chinese_label(file_path: Path | str) -> str:
    path = Path(file_path)
    chinese_parts = CHINESE_PATTERN.findall(path.stem)
    if chinese_parts:
        return "_".join(chinese_parts)
    return path.stem.removeprefix("cleaned_")


def build_chart_display_label(keyword: str, files: list[Path]) -> str:
    canonical_keyword = KEYWORD_ALIAS_TO_GROUP.get(keyword, keyword)
    if canonical_keyword in COMBINED_KEYWORD_GROUPS:
        return canonical_keyword

    labels: list[str] = []
    for file_path in files:
        label = extract_chinese_label(file_path)
        if label not in labels:
            labels.append(label)
    if labels:
        return "_".join(labels)
    return canonical_keyword


def attach_chart_timestamp(
    records: list[dict[str, Any]],
    timestamp_field: str = "timestamp",
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in records:
        item = dict(row)
        item["_chart_timestamp"] = parse_timestamp(str(row.get(timestamp_field, "")).strip())
        enriched.append(item)
    return enriched


def filter_records_by_period(
    records: list[dict[str, Any]],
    *,
    period_type: str,
    target_date: str,
    target_month: str,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in records:
        timestamp = row.get("_chart_timestamp")
        if timestamp is None:
            continue
        if period_type == "day" and timestamp.strftime("%Y-%m-%d") == target_date:
            filtered.append(row)
        elif period_type == "month" and timestamp.strftime("%Y-%m") == target_month:
            filtered.append(row)
    return filtered


def detect_numeric_fields(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return []

    candidate_fields = [
        key for key in records[0].keys() if key not in {"timestamp", "数据源", "_chart_timestamp"}
    ]
    numeric_fields: list[str] = []
    for field in candidate_fields:
        has_numeric = False
        for row in records:
            value = row.get(field)
            if value in (None, ""):
                continue
            parsed = _to_float(value)
            if parsed is not None:
                has_numeric = True
                break
            has_numeric = False
            break
        if has_numeric:
            numeric_fields.append(field)
    return numeric_fields


def to_export_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exported: list[dict[str, Any]] = []
    for row in records:
        item = dict(row)
        item.pop("_chart_timestamp", None)
        exported.append(item)
    return exported


def build_chart_output_name(base_label: str, period_type: str, target_label: str) -> str:
    timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_label}_{target_label}_{timestamp_suffix}.png"


def build_filtered_csv_name(file_path: Path, period_type: str, target_label: str) -> str:
    return f"{file_path.stem}_{period_type}_{target_label}.csv"


def _build_series_with_gaps(
    records: list[dict[str, Any]],
    field: str,
    *,
    gap_threshold: timedelta = GAP_BREAK_THRESHOLD,
) -> tuple[list[datetime], list[float]]:
    timestamps: list[datetime] = []
    values: list[float] = []
    previous_timestamp: datetime | None = None

    for row in records:
        current_timestamp = row["_chart_timestamp"]
        if previous_timestamp is not None and current_timestamp - previous_timestamp > gap_threshold:
            timestamps.append(current_timestamp)
            values.append(float("nan"))

        value = row.get(field)
        timestamps.append(current_timestamp)
        parsed = _to_float(value)
        values.append(parsed if parsed is not None else float("nan"))
        previous_timestamp = current_timestamp

    return timestamps, values


def _resolve_dual_axis_fields(numeric_fields: list[str]) -> tuple[str | None, str | None]:
    left_field = next((field for field in numeric_fields if "deg_c" in field.lower()), None)
    right_field = next((field for field in numeric_fields if "%rh" in field.lower()), None)
    return left_field, right_field


def _display_label(field: str, field_labels: dict[str, str] | None = None) -> str:
    if field_labels and field in field_labels:
        return field_labels[field]
    return field


def plot_time_series_chart(
    records: list[dict[str, Any]],
    *,
    numeric_fields: list[str],
    title: str,
    output_path: Path | str,
    field_labels: dict[str, str] | None = None,
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))
    left_field, right_field = _resolve_dual_axis_fields(numeric_fields)

    if left_field and right_field:
        left_times, left_values = _build_series_with_gaps(records, left_field)
        right_times, right_values = _build_series_with_gaps(records, right_field)
        left_label = _display_label(left_field, field_labels)
        right_label = _display_label(right_field, field_labels)

        left_line = ax.plot(left_times, left_values, linewidth=1.2, color="#d55e00", label=left_label)[0]
        ax.set_ylabel(left_label, color="#d55e00")
        ax.tick_params(axis="y", labelcolor="#d55e00")

        ax_right = ax.twinx()
        right_line = ax_right.plot(
            right_times,
            right_values,
            linewidth=1.2,
            color="#0072b2",
            label=right_label,
        )[0]
        ax_right.set_ylabel(right_label, color="#0072b2")
        ax_right.tick_params(axis="y", labelcolor="#0072b2")
        ax.legend([left_line, right_line], [left_label, right_label], loc="upper left")
    else:
        for field in numeric_fields:
            timestamps, values = _build_series_with_gaps(records, field)
            ax.plot(timestamps, values, linewidth=1.2, label=_display_label(field, field_labels))
        ax.set_ylabel("数值")
        ax.legend()

    ax.set_title(title)
    ax.set_xlabel("时间")
    ax.grid(True, linestyle="--", alpha=0.3)

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter("%Y-%m-%d\n%H:%M")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_missing_data_placeholder(
    *,
    title: str,
    output_path: Path | str,
    numeric_fields: list[str],
    target_label: str,
    field_labels: dict[str, str] | None = None,
    message: str = "缺少原始数据",
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))
    left_field, right_field = _resolve_dual_axis_fields(numeric_fields)

    ax.set_title(title)
    ax.set_xlabel("时间")
    ax.grid(True, linestyle="--", alpha=0.3)

    if left_field and right_field:
        left_label = _display_label(left_field, field_labels)
        right_label = _display_label(right_field, field_labels)
        ax.set_ylabel(left_label, color="#d55e00")
        ax.tick_params(axis="y", labelcolor="#d55e00")

        ax_right = ax.twinx()
        ax_right.set_ylabel(right_label, color="#0072b2")
        ax_right.tick_params(axis="y", labelcolor="#0072b2")

        left_handle = Line2D([0], [0], color="#d55e00", linewidth=1.2, label=left_label)
        right_handle = Line2D([0], [0], color="#0072b2", linewidth=1.2, label=right_label)
        ax.legend([left_handle, right_handle], [left_label, right_label], loc="upper left")
    else:
        y_label = _display_label(numeric_fields[0], field_labels) if numeric_fields else "数值"
        ax.set_ylabel(y_label)
        handles = [
            Line2D([0], [0], linewidth=1.2, label=_display_label(field, field_labels))
            for field in numeric_fields
        ]
        if handles:
            ax.legend(handles=handles, loc="upper left")

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter("%Y-%m-%d\n%H:%M")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    start_dt = datetime.strptime(f"{target_label} 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(f"{target_label} 23:59:59", "%Y-%m-%d %H:%M:%S")
    ax.set_xlim(start_dt, end_dt)

    ax.text(
        0.5,
        0.5,
        message,
        color="red",
        fontsize=30,
        fontweight="bold",
        rotation=45,
        ha="center",
        va="center",
        transform=ax.transAxes,
        alpha=0.85,
    )
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
