from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _parse_audit_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed = []
    for row in rows:
        result_raw = row.get("result", "{}")
        try:
            result_obj = json.loads(result_raw)
        except json.JSONDecodeError:
            result_obj = {"raw": result_raw}
        parsed.append({"check_name": row.get("check_name", ""), "result": result_obj})
    return parsed


def _extract_critical_findings(parsed_audit: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for row in parsed_audit:
        check_name = row["check_name"]
        result = row["result"]

        # Report only non-zero indicators as potential issues.
        numeric_values = [v for v in result.values() if isinstance(v, (int, float))]
        if any(v not in (0, 0.0) for v in numeric_values):
            findings.append(f"- {check_name}: {result}")

    if not findings:
        findings.append("- No non-zero anomaly indicators were found in the configured audit summary checks.")
    return findings


def _format_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows]
    return [line, sep, *body]


def build_round1_markdown_report(output_dir: Path, report_path: Path) -> None:
    ingest_rows = _read_csv(output_dir / "ingest_log.csv")
    audit_rows = _read_csv(output_dir / "audit_summary.csv")
    mcq_rows = _read_csv(output_dir / "mcq_results.csv")
    choice_rows = _read_csv(output_dir / "mcq_choice_answers.csv")

    parsed_audit = _parse_audit_summary(audit_rows)
    critical_findings = _extract_critical_findings(parsed_audit)

    lines: list[str] = []
    lines.append("# Round 1 Data Audit and MCQ Report")
    lines.append("")
    lines.append("## 1. Warehouse Ingestion")
    lines.append(f"- Tables ingested: {len(ingest_rows)}")
    if ingest_rows:
        total_rows = sum(int(r.get("row_count", 0) or 0) for r in ingest_rows)
        lines.append(f"- Total rows loaded: {total_rows}")

    if ingest_rows:
        top_tables = sorted(ingest_rows, key=lambda x: int(x.get("row_count", 0) or 0), reverse=True)[:5]
        lines.append("")
        lines.extend(
            _format_table(
                ["table_name", "source_file", "row_count", "column_count"],
                [
                    [
                        str(r.get("table_name", "")),
                        str(r.get("source_file", "")),
                        str(r.get("row_count", "")),
                        str(r.get("column_count", "")),
                    ]
                    for r in top_tables
                ],
            )
        )

    lines.append("")
    lines.append("## 2. Data Audit Summary")
    lines.extend(critical_findings)

    lines.append("")
    lines.append("## 3. MCQ Computed Results")
    if mcq_rows:
        lines.extend(
            _format_table(
                ["question_id", "metric_name", "metric_value", "note"],
                [
                    [
                        str(r.get("question_id", "")),
                        str(r.get("metric_name", "")),
                        str(r.get("metric_value", "")),
                        str(r.get("note", "")),
                    ]
                    for r in mcq_rows
                ],
            )
        )
    else:
        lines.append("- No MCQ results found.")

    lines.append("")
    lines.append("## 4. MCQ Choice Mapping")
    if choice_rows:
        lines.extend(
            _format_table(
                ["question_id", "metric_value", "selected_choice", "choice_reason"],
                [
                    [
                        str(r.get("question_id", "")),
                        str(r.get("metric_value", "")),
                        str(r.get("selected_choice", "")),
                        str(r.get("choice_reason", "")),
                    ]
                    for r in choice_rows
                    if str(r.get("question_id", "")).startswith("Q")
                ],
            )
        )
    else:
        lines.append("- No choice mapping output found. Run the choice mapping script first.")

    lines.append("")
    lines.append("## 5. Notes")
    lines.append("- Q5 uses promo_id OR promo_id_2 to determine whether a line item has promotion.")
    lines.append("- Q7 excludes cancelled/returned/failed-like order statuses when computing regional revenue.")
    lines.append("- Q8 checks payment_method consistency between orders and payments before mode selection.")
    lines.append("- Q9 return rate is calculated by record count, not quantity.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
