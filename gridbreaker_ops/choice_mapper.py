from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .common import write_csv_rows


def default_choice_key() -> dict[str, Any]:
    return {
        "Q1": {
            "A": 30,
            "B": 90,
            "C": 180,
            "D": 365,
            "rule": "nearest_number",
        },
        "Q2": {
            "A": "Premium",
            "B": "Budget",
            "C": "Luxury",
            "D": "Standard",
            "rule": "exact_text",
        },
        "Q3": {
            "A": "defective_item",
            "B": "wrong_size",
            "C": "late_delivery",
            "D": "changed_mind",
            "rule": "exact_text",
        },
        "Q4": {
            "A": "organic_search",
            "B": "paid_search",
            "C": "email_campaign",
            "D": "social_media",
            "rule": "exact_text",
        },
        "Q5": {
            "A": 0.19,
            "B": 0.27,
            "C": 0.39,
            "D": 0.48,
            "rule": "nearest_number",
        },
        "Q6": {
            "A": "55+",
            "B": "18-24",
            "C": "25-34",
            "D": "35-44",
            "rule": "exact_text",
        },
        "Q7": {
            "A": "North",
            "B": "South",
            "C": "East",
            "D": "West",
            "rule": "exact_text",
        },
        "Q8": {
            "A": "credit_card",
            "B": "cod",
            "C": "bank_transfer",
            "D": "e_wallet",
            "rule": "exact_text",
        },
        "Q9": {
            "A": "S",
            "B": "M",
            "C": "L",
            "D": "XL",
            "rule": "exact_text",
        },
        "Q10": {
            "A": 1,
            "B": 3,
            "C": 6,
            "D": 12,
            "rule": "nearest_number",
        },
    }


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _parse_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_single_choice(metric_value: Any, choice_options: dict[str, Any], rule: str) -> tuple[str, str]:
    option_pairs = [(k, v) for k, v in choice_options.items() if k in {"A", "B", "C", "D"}]
    if not option_pairs:
        return "UNMAPPED", "No A/B/C/D options found"

    if rule == "nearest_number":
        metric_num = _parse_float(metric_value)
        if metric_num is None:
            return "UNMAPPED", "Metric value is not numeric"

        distances: list[tuple[str, float]] = []
        for opt, opt_val in option_pairs:
            parsed = _parse_float(opt_val)
            if parsed is None:
                continue
            distances.append((opt, abs(metric_num - parsed)))

        if not distances:
            return "UNMAPPED", "No numeric options for nearest_number rule"

        best = sorted(distances, key=lambda x: (x[1], x[0]))[0]
        return best[0], f"nearest_number distance={best[1]:.6f}"

    metric_txt = _normalize_text(metric_value)
    for opt, opt_val in option_pairs:
        if metric_txt == _normalize_text(opt_val):
            return opt, "exact_text matched"
    return "UNMAPPED", "No exact text match"


def load_mcq_rows(mcq_csv: Path) -> list[dict[str, Any]]:
    with mcq_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def map_mcq_choices(mcq_rows: list[dict[str, Any]], choice_key: dict[str, Any]) -> list[dict[str, Any]]:
    mapped_rows: list[dict[str, Any]] = []

    for row in mcq_rows:
        qid = row.get("question_id", "")
        metric_value = row.get("metric_value")

        if qid not in choice_key:
            mapped_rows.append(
                {
                    **row,
                    "selected_choice": "UNMAPPED",
                    "choice_reason": "Question is not in choice key",
                }
            )
            continue

        option_block = choice_key[qid]
        rule = option_block.get("rule", "exact_text")
        selected_choice, reason = _map_single_choice(metric_value, option_block, rule)
        mapped_rows.append(
            {
                **row,
                "selected_choice": selected_choice,
                "choice_reason": reason,
            }
        )

    return mapped_rows


def write_choice_outputs(output_dir: Path, mapped_rows: list[dict[str, Any]]) -> None:
    write_csv_rows(output_dir / "mcq_choice_answers.csv", mapped_rows)
    (output_dir / "mcq_choice_answers.json").write_text(
        json.dumps(mapped_rows, indent=2, default=str),
        encoding="utf-8",
    )


def ensure_choice_key_file(choice_key_path: Path) -> dict[str, Any]:
    if not choice_key_path.exists():
        defaults = default_choice_key()
        choice_key_path.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
        return defaults

    return json.loads(choice_key_path.read_text(encoding="utf-8"))
