"""入口启动辅助模块。

使用说明:
- 解决直接运行入口脚本时 `src` 布局下的导入路径问题。
- 当入口文件通过 `python xxx.py` 直接执行时，会先调用这里的 `ensure_src_on_path()`。
- 不单独运行本文件。
"""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_on_path() -> None:
    current_file = Path(__file__).resolve()
    src_dir = current_file.parents[2]
    src_text = str(src_dir)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
