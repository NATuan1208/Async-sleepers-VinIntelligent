from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import duckdb

FAILED_ORDER_STATUSES = (
    "cancelled",
    "canceled",
    "returned",
    "failed",
    "payment_failed",
    "delivery_failed",
    "refunded",
)


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def run_query(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    result = con.execute(sql)
    cols = [c[0] for c in result.description]
    rows = result.fetchall()
    return [dict(zip(cols, row)) for row in rows]


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
