"""报表生成入口。

使用说明:
- 用于读取输入目录中的 CSV 数据，汇总后生成报表文件。
- 支持两种运行方式:
  `python -m chiller_plant_control_data.entries.generate_report`
  `python src/chiller_plant_control_data/entries/generate_report.py`
- 输出位于 `output/reports/`。
"""

from __future__ import annotations

from pprint import pprint

if __package__ in (None, ""):
    from _bootstrap import ensure_src_on_path

    ensure_src_on_path()

from chiller_plant_control_data.entries._shared import run_entry
from chiller_plant_control_data.flows.report_flow import run


if __name__ == "__main__":
    pprint(run_entry("generate_report", run))
