from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import duckdb

from gridbreaker_ops.audit import run_audit_pack
from gridbreaker_ops.common import ensure_output_dir, write_csv_rows
from gridbreaker_ops.mcq import persist_mcq_results, solve_mcqs
from gridbreaker_ops.warehouse import ingest_csvs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Round 1 local warehouse, data audit, and MCQ solver")
    parser.add_argument("--data-dir", default="Data", help="Directory containing input CSV files")
    parser.add_argument("--db-path", default="gridbreaker.duckdb", help="DuckDB database file path")
    parser.add_argument("--output-dir", default="outputs_round1", help="Directory for generated outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    db_path = Path(args.db_path).resolve()
    output_dir = Path(args.output_dir).resolve()

    ensure_output_dir(output_dir)

    con = duckdb.connect(str(db_path))
    try:
        ingest_log = ingest_csvs(con, data_dir)
        write_csv_rows(output_dir / "ingest_log.csv", ingest_log)

        audit_results = run_audit_pack(con, output_dir)
        mcq_results = solve_mcqs(con)
        persist_mcq_results(output_dir, mcq_results)

        run_meta = {
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "db_path": str(db_path),
            "data_dir": str(data_dir),
            "output_dir": str(output_dir),
            "tables_ingested": len(ingest_log),
            "audit_checks": len(audit_results),
            "mcq_records": len(mcq_results),
        }
        (output_dir / "run_meta.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

        print("Round 1 pipeline completed successfully.")
        print(f"DB: {db_path}")
        print(f"Outputs: {output_dir}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
