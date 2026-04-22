from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from .common import qident


def ingest_csvs(con: duckdb.DuckDBPyConnection, data_dir: Path) -> list[dict[str, Any]]:
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS round1_ingest_log (
            table_name VARCHAR,
            source_file VARCHAR,
            loaded_at TIMESTAMP,
            row_count BIGINT,
            column_count BIGINT
        )
        """
    )
    con.execute("DELETE FROM round1_ingest_log")

    logs: list[dict[str, Any]] = []
    loaded_at = datetime.now().isoformat(timespec="seconds")

    for csv_path in csv_files:
        table_name = csv_path.stem.lower()
        table_ident = qident(table_name)

        con.execute(
            f"""
            CREATE OR REPLACE TABLE {table_ident} AS
            SELECT *
            FROM read_csv_auto(?, header = true, sample_size = -1)
            """,
            [str(csv_path)],
        )

        row_count = con.execute(f"SELECT COUNT(*) FROM {table_ident}").fetchone()[0]
        col_count = con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE lower(table_name) = lower(?)
            """,
            [table_name],
        ).fetchone()[0]

        con.execute(
            """
            INSERT INTO round1_ingest_log(table_name, source_file, loaded_at, row_count, column_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            [table_name, csv_path.name, loaded_at, row_count, col_count],
        )

        logs.append(
            {
                "table_name": table_name,
                "source_file": csv_path.name,
                "loaded_at": loaded_at,
                "row_count": row_count,
                "column_count": col_count,
            }
        )

    return logs
