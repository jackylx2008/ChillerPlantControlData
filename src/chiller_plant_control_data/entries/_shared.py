from __future__ import annotations

from pathlib import Path
from typing import Callable

from chiller_plant_control_data.config_loader import load_config
from chiller_plant_control_data.context import AppContext
from chiller_plant_control_data.logging_config import get_logger, setup_logger
from chiller_plant_control_data.modules.path_utils import ensure_directory


def run_entry(entry_name: str, flow_runner: Callable[[AppContext], dict[str, object]]) -> dict[str, object]:
    project_root = Path.cwd()
    config = load_config(project_root / "config.yaml", project_root / "common.env")

    output_dir = ensure_directory(project_root / config.get("app", {}).get("output_dir", "output"))
    log_dir = ensure_directory(project_root / "log")

    setup_logger(
        log_level=config.get("app", {}).get("log_level", "INFO"),
        log_dir=log_dir,
        log_name=entry_name,
    )

    context = AppContext(
        project_root=project_root,
        config=config,
        entry_name=entry_name,
        output_dir=output_dir,
        log_dir=log_dir,
    )

    logger = get_logger(__name__)
    logger.info("Entry started: %s", entry_name)
    result = flow_runner(context)
    logger.info("Entry finished: %s", result)
    return result

