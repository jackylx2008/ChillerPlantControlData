from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def read_csv_records(file_path: Path | str, encoding: str = "utf-8-sig") -> list[dict[str, Any]]:
    path = Path(file_path)
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def write_csv_records(file_path: Path | str, rows: list[dict[str, Any]]) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

