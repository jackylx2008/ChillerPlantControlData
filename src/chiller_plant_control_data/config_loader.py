"""Configuration loading with env-file injection and ${VAR:-default} expansion."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(?::-(.*?))?\}")


def load_env_file(env_file: str | Path) -> None:
    """Load simple KEY=VALUE pairs into process env if not already set."""
    path = Path(env_file)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _expand_env_in_text(raw_text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        env_name = match.group(1)
        default_value = match.group(2) or ""
        return os.getenv(env_name, default_value)

    return ENV_PATTERN.sub(replace, raw_text)


def load_config(
    config_file: str | Path = "config.yaml",
    env_file: str | Path = "common.env",
) -> dict[str, Any]:
    """Load YAML config after injecting local env values and expanding placeholders."""
    load_env_file(env_file)
    config_path = Path(config_file)
    raw_text = config_path.read_text(encoding="utf-8")
    expanded_text = _expand_env_in_text(raw_text)
    data = yaml.safe_load(expanded_text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")
    return data

