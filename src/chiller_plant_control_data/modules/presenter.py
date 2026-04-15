from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def format_table(rows: list[dict[str, Any]], limit: int = 20) -> str:
    if not rows:
        return "No data."

    limited = rows[:limit]
    headers = list(limited[0].keys())
    widths = {
        header: max(len(header), *(len(str(row.get(header, ""))) for row in limited))
        for header in headers
    }

    def line(row: dict[str, Any]) -> str:
        return " | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)

    separator = "-+-".join("-" * widths[header] for header in headers)
    output = [line({header: header for header in headers}), separator]
    output.extend(line(row) for row in limited)
    return "\n".join(output)


def write_json(file_path: Path | str, payload: Any) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

