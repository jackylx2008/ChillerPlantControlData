"""入口共享启动模块。

使用说明:
- 提供 `run_entry()`，负责统一完成配置加载、上下文创建、日志初始化和 flow 调用。
- `entries/` 下的各入口脚本都会调用这里的方法。
- 不单独运行本文件。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from chiller_plant_control_data.config_loader import load_config
from chiller_plant_control_data.context import AppContext, build_context
from chiller_plant_control_data.logging_config import get_logger, setup_logger


def run_entry(
    entry_name: str,
    flow_runner: Callable[[AppContext], dict[str, object]],
    **metadata: Any,
) -> dict[str, object]:
    project_root = Path.cwd()
    config = load_config(project_root / "config.yaml", project_root / "common.env")
    context = build_context(config=config, entry_name=entry_name, project_root=project_root, **metadata)
    context.ensure_runtime_dirs()

    setup_logger(
        log_level=config.get("app", {}).get("log_level", "INFO"),
        log_dir=context.log_dir,
        log_file_name=f"{entry_name}.log",
    )

    logger = get_logger(__name__)
    logger.info("Entry started: %s", entry_name)
    result = flow_runner(context)
    logger.info("Entry finished: %s", result)
    return result
