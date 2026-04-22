# CLAUDE.md — DATATHON 2026 Shadow P&L (Gridbreaker Team)

## Status
- **Phase 1 (Data Engine + MCQ):** COMPLETE
- **Phase 2 (Shadow P&L EDA):** COMPLETE — Acts 1–5 executed, 15 charts, 7 audit entries, feature CSV exported
- **Phase 3 (ML / Forecasting):** NEXT — uses `outputs_round1/features_for_part3.csv`

## Context
10-year (2012-2022) Vietnamese fashion e-commerce. All Phase 1+2 outputs in `outputs_round1/`.
Master brief: `CLAUDE_CODE_SHADOW_PNL_BRIEF.md`. Rules: `PROJECT_BASED_KNOWLEDGE.md`.
EDA report: `SHADOW_PNL_EDA_REPORT.md`

## Phase 2 Key Findings (for Phase 3 context)
- **True Net = 117 triệu VND (0.7% of 16.43 tỷ gross)** — COGS 86.2% is the dominant leak
- Surgical recovery opportunity: **588 triệu VND** (Wave 1 discount 61M + Wave 2 returns 82M + Wave 3 stockout 445M)
- CC cancellation: 36M additional (not in wave total — confidence too low)
- Logistic regression AUC = 0.5 (reviews have zero predictive value for returns — honest null result)
- Act 2 LEAST() tautology fixed in Act 3D: phantom = 445M (not 890M)
- Anti-leakage train/val split: train ≤ 2019, val ≥ 2020-02, 31-day buffer ✅

## Data
- 14 CSVs in `Data/` (sales, orders, order_items, products, customers, geography,
  inventory, payments, promotions, returns, reviews, shipments, web_traffic, sample_submission)
- Audit result: CLEAN (no orphans, no missing dates, no COGS violations)
  - Exception: 16 duplicate order_items natural keys (minor)
  - 14.8% cancelled/returned orders (646,945 total orders)

## Hard Rules (non-negotiable)

### DuckDB-First
All aggregations/joins >10K rows → SQL via `con.execute(...).df()`. No bulk Pandas CSV reads.
Single `con` per notebook. Pattern in `warehouse.py`.

### VND Audit (Rule #1)
No VND number in markdown without code computing it.
- All formatting: `format_vnd()` from `shadow_pnl_style.py`
- All recommendation impacts: `vnd_impact()` → logs to `outputs_round1/shadow_pnl_audit.csv`
- Sanity range: 100K VND ≤ impact ≤ 1,000 tỷ VND (catches 1000x unit errors like v1 bug)

### MCQ Definitions (must match exactly)
| Metric | Rule |
|--------|------|
| Promo/discount | `promo_id IS NOT NULL OR promo_id_2 IS NOT NULL` |
| Regional revenue | EXCLUDE cancelled + returned statuses |
| Cancelled payment mode | Cross-check orders vs payments (100% match confirmed) → credit_card |
| Return rate | COUNT(returns) / COUNT(order_items) by RECORD, not quantity |
| Size highest return | S (by record count) |

### Style Enforcement
Every notebook cell 1:
```python
import sys; sys.path.insert(0, '.')
from shadow_pnl_style import (apply_shadow_pnl_style, SHADOW_PNL_COLORS,
    format_vnd, format_pct, vnd_impact, init_audit_log, finalize_chart)
apply_shadow_pnl_style()
init_audit_log()
```
Colors only from `SHADOW_PNL_COLORS`. Chart titles = INSIGHT sentences, not data descriptions.

### Anti-Leakage (Act 4)
`assert train.max_date + timedelta(30) < val.min_date` before any time-series work.

## Notebooks (COMPLETE)
- `notebooks/01_shadow_pnl_foundation.ipynb` — Act 1 (Illusion) + Act 2 (Unmasking / Hero Waterfall) ✅
- `notebooks/02_shadow_pnl_investigation.ipynb` — Act 3 (Forensics) + Act 4 (Trajectory) + Act 5 (Scalpel) ✅

## Phase 3 Inputs
- `outputs_round1/features_for_part3.csv` — 7 features with lag/source metadata
  - `return_rate_roll30_lag7` (HIGH importance)
  - `discount_rate_roll30_lag14` (HIGH importance)
  - `review_rating_shift30_lag14` (MEDIUM)
  - `stockout_days_roll30_lag7` (MEDIUM)
  - `cogs_margin_roll90_lag30` (HIGH — most impactful)
  - `cancel_rate_roll30_lag14` (LOW)
  - `web_sessions_roll30_lag14` (MEDIUM)
- Anti-leakage split: train 2012–2019, val 2020–2022

## init_audit_log — Path Fix
Always call `init_audit_log(Path('../outputs_round1/shadow_pnl_audit.csv'))` explicitly in notebooks.
Default path in `shadow_pnl_style.py` is relative and resolves wrong from `notebooks/` subdirectory.

## Missing File
`eda_data_sample.md` not found in repo. Schema reference: read CSVs directly or see brief Part B.3.
