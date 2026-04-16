"""路径辅助模块。

使用说明:
- 提供目录创建等简单路径工具函数。
- 供入口层或基础模块复用。
- 不直接运行本文件。
"""

from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path | str) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
