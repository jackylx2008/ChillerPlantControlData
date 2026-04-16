"""数据清洗入口。

使用说明:
- 用于读取 `INPUT_PATH` 指向的 CSV 文件或目录，并输出清洗后的结果到 `output/cleaned/`。
- 支持两种运行方式:
  `python -m chiller_plant_control_data.entries.clean_data`
  `python src/chiller_plant_control_data/entries/clean_data.py`
- 运行前会清空 `output/cleaned/`。
"""

from __future__ import annotations

from pprint import pprint

if __package__ in (None, ""):
    from _bootstrap import ensure_src_on_path

    ensure_src_on_path()

from chiller_plant_control_data.entries._shared import run_entry
from chiller_plant_control_data.flows.clean_data_flow import run


if __name__ == "__main__":
    pprint(run_entry("clean_data", run))
