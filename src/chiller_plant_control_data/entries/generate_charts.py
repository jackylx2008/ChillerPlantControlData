"""图表展示入口。

使用说明:
- 从 `output/cleaned/` 中按关键字匹配清洗后的 CSV 文件。
- 支持按某一天或某一个月筛选数据后生成 PNG 图表和对应筛选 CSV。
- 常用示例:
  `python src/chiller_plant_control_data/entries/generate_charts.py --keyword 总供水温度 --period-type day --target-date 2025-09-27`
  `python src/chiller_plant_control_data/entries/generate_charts.py --keyword 室外温湿度趋势数据 --period-type month --target-month 2025-07`
- 支持两种运行方式:
  `python -m chiller_plant_control_data.entries.generate_charts`
  `python src/chiller_plant_control_data/entries/generate_charts.py`
"""

from __future__ import annotations

import argparse
from pprint import pprint

if __package__ in (None, ""):
    from _bootstrap import ensure_src_on_path

    ensure_src_on_path()

from chiller_plant_control_data.entries._shared import run_entry
from chiller_plant_control_data.flows.generate_charts_flow import run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按关键词和时间范围生成清洗后数据图表。")
    parser.add_argument("--keyword", required=True, help="用于匹配清洗后文件名的关键字。")
    parser.add_argument(
        "--period-type",
        choices=("day", "month"),
        required=True,
        help="图表筛选周期类型。",
    )
    parser.add_argument("--target-date", help="当 period-type=day 时使用，格式 YYYY-MM-DD。")
    parser.add_argument("--target-month", help="当 period-type=month 时使用，格式 YYYY-MM。")
    parser.add_argument("--cleaned-dir", help="清洗后 CSV 所在目录，默认使用配置值。")
    parser.add_argument("--file-glob", help="清洗后文件匹配模式，默认使用配置值。")
    parser.add_argument("--timestamp-field", help="时间字段名，默认使用配置值。")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.period_type == "day" and not args.target_date:
        raise SystemExit("--period-type=day 时必须提供 --target-date")
    if args.period_type == "month" and not args.target_month:
        raise SystemExit("--period-type=month 时必须提供 --target-month")

    pprint(
        run_entry(
            "generate_charts",
            run,
            keyword=args.keyword,
            period_type=args.period_type,
            target_date=args.target_date,
            target_month=args.target_month,
            cleaned_dir=args.cleaned_dir,
            file_glob=args.file_glob,
            timestamp_field=args.timestamp_field,
        )
    )
