"""运行上下文模块。

使用说明:
- 提供 `AppContext`，在入口层、编排层、基础模块之间共享配置和路径。
- 入口脚本通常通过 `build_context()` 创建上下文对象。
- 不直接运行本文件。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppContext:
    """Runtime context shared across application layers."""

    project_root: Path
    config: dict[str, Any]
    entry_name: str
    logger_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def app_config(self) -> dict[str, Any]:
        return self.config.get("app", {})

    @property
    def flows_config(self) -> dict[str, Any]:
        return self.config.get("flows", {})

    @property
    def entry_flow_config(self) -> dict[str, Any]:
        return self.flows_config.get(self.entry_name, {})

    @property
    def input_path(self) -> Path:
        raw_value = self.app_config.get("input_path", "data/input")
        return (self.project_root / raw_value).resolve()

    @property
    def output_dir(self) -> Path:
        raw_value = self.app_config.get("output_dir", "output")
        return (self.project_root / raw_value).resolve()

    @property
    def log_dir(self) -> Path:
        raw_value = self.app_config.get("log_dir", "log")
        return (self.project_root / raw_value).resolve()

    def flow_config(self, flow_name: str) -> dict[str, Any]:
        return self.flows_config.get(flow_name, {})

    def ensure_runtime_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


def build_context(
    config: dict[str, Any],
    entry_name: str,
    project_root: str | Path | None = None,
    **metadata: Any,
) -> AppContext:
    root = Path(project_root or Path.cwd()).resolve()
    return AppContext(
        project_root=root,
        config=config,
        entry_name=entry_name,
        logger_name=metadata.pop("logger_name", None),
        metadata=metadata,
    )
