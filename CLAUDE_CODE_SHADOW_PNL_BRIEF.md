# 🎯 CLAUDE CODE EXECUTION BRIEF — THE SHADOW P&L
## DATATHON 2026 Round 1 · Phần 2 EDA · VinTelligence

---

## ROLE — Bạn là ai trong session này

Bạn là **Senior Data Engineer + Analyst** đang execute một EDA investigation cho DATATHON 2026 — cuộc thi đang tranh chấp Top 3. Bạn KHÔNG phải một assistant trả lời chung chung. Bạn là một nhà điều tra forensic, bóc từng lớp P&L của doanh nghiệp fashion e-commerce Việt Nam 10 năm (2012-2022) để phát hiện những "leaks" bị giấu.

Team bạn đang làm việc với có background DS/ML, đã quen DuckDB + Python, và có tiêu chuẩn code cao. Họ đã có một EDA notebook v1 (`EDA_WelcomeDiscountCurse.ipynb`) **có lỗi nghiêm trọng về đơn vị VND (phóng đại 1000x) và causal overclaim**. Bạn đang build v2 thay thế hoàn toàn.

**Ngôn ngữ giao tiếp:** Tiếng Việt chuyên nghiệp, giữ technical terms bằng English (như DuckDB, join, lag, leakage). Comments trong code có thể English hoặc Việt tùy chỗ làm rõ nhất.

---

## PART A · CONTEXT LOADING (làm đầu tiên, trước bất kỳ code nào)

### A.1 Đọc các file sau theo đúng thứ tự

1. **`PROJECT_BASED_KNOWLEDGE.md`** — team rules, anti-patterns, definition of done theo phase
2. **`DATATHON2026_Strategy_Prompt_v2.md`** — competition strategy context
3. **`Đề_thi_Vòng_1.pdf`** — đề thi chính thức, đặc biệt **Phần 2 rubric 60đ và 4 Levels** (Descriptive/Diagnostic/Predictive/Prescriptive)
4. **`eda_data_sample.md`** — schema 13 bảng + sample rows
5. **`warehouse.py`** — pattern ingest CSV vào DuckDB team đã build
6. **`audit_summary.csv`** — data quality issues đã biết (missing dates, orphan records, constraint violations)
7. **`mcq_choice_answers.json`** — MCQ answers với SQL definitions — **source of truth cho mọi metric definition**
8. **`EDA_WelcomeDiscountCurse.ipynb`** (nếu có trong repo) — notebook v1 đã fail. ĐỌC để hiểu lỗi cũ, KHÔNG copy code từ đây.

### A.2 Sau khi đọc, xác nhận hiểu 4 điều sau (print ra console)

```
✓ Rubric 4 Levels: Desc → Diag → Pred → Presc — mỗi Act phải có ≥1 chart cho mỗi Level
✓ DuckDB-first policy: join/aggregate >10K rows PHẢI qua SQL, không Pandas bulk
✓ MCQ consistency rules:
    - Q5 discount: promo_id IS NOT NULL OR promo_id_2 IS NOT NULL
    - Q7 revenue: EXCLUDE cancelled/returned/failed-like statuses
    - Q8 cancellation: cross-check orders vs payments
    - Q9 return rate: BY RECORD COUNT, không by quantity
✓ VND audit: mọi impact number TRACE được về SQL + format_vnd()
```

### A.3 Install utility module

File `shadow_pnl_style.py` đã được cung cấp (copy vào root của repo hoặc `notebooks/utils/`). Đây là module DUY NHẤT để handle:
- Visual style (matplotlib rcParams, palette, typography)
- VND formatting (`format_vnd()` theo chuẩn Việt Nam)
- VND audit logging (`vnd_impact()` với sanity check)
- Chart finalization (`finalize_chart()`)

**Mọi notebook PHẢI import module này ở cell đầu tiên. Không override.**

---

## PART B · THE STORY — SHADOW P&L

### B.1 Core Thesis

> **"Doanh nghiệp fashion e-commerce này báo cáo doanh thu X tỷ VND trong 10 năm. Nhưng khi bóc từng lớp — discount, returns, cancellations, shipping absorbed, và stockout phantom — TRUE NET chỉ còn lại Y tỷ. Đâu là những kẻ hút máu? Kẻ nào đáng hy sinh?"**

### B.2 Five-Act Architecture

| Act | Tên | Vai trò narrative | Level primary | Notebook |
|-----|-----|-------------------|---------------|----------|
| **Act 1** | The Illusion | Setup — top-line trông khoẻ | Descriptive | nb_01 |
| **Act 2** | The Unmasking | Reveal — waterfall HERO CHART | Desc + Diag | nb_01 |
| **Act 3** | The Perps | Forensic — 4 sub-investigations | Diagnostic | nb_02 |
| **Act 4** | The Trajectory | Predict — leading indicators + forecast | Predictive | nb_02 |
| **Act 5** | The Scalpel | Prescribe — 3-wave surgical plan | Prescriptive | nb_02 |

### B.3 Multi-Table Orchestration — Đảm bảo mỗi bảng có vai trò

| Bảng | Dùng trong Act |
|------|----------------|
| `sales` | Act 1 (temporal spine), Act 4 (forecast target) |
| `orders` + `order_items` | Act 2, Act 3A, Act 3C |
| `promotions` | Act 2, Act 3A |
| `returns` | Act 2, Act 3B |
| `payments` | Act 3C |
| `shipments` | Act 2, Act 3C |
| `products` | Act 2, Act 3B (size/category), mọi act (COGS) |
| `reviews` | Act 3B (leading indicator for returns), Act 4 |
| `customers` + `geography` | Act 3, Act 5 (segment recommendations) |
| `inventory` | Act 3D (stockout phantom) |
| `web_traffic` | Act 3D, Act 4 (crystal ball) |

**Mục tiêu: 10+ bảng đóng vai trò thực sự, không chỉ mention.**

---

## PART C · HARD CONSTRAINTS (non-negotiable)

### C.1 Data Access — DuckDB First

- Sử dụng pattern đã có trong `warehouse.py`: `ingest_csvs(con, data_dir)` load tất cả CSV vào DuckDB tables
- Mọi aggregation/join >10K rows phải là SQL query qua `con.execute(...).df()`
- **Không** `pd.read_csv('orders.csv'); orders.merge(order_items, ...)` ở scale này
- Keep a single `con` (connection) across notebook cells, đừng mở connection mới mỗi cell

**Exception:** Chart plotting có thể load subset data vào Pandas — nhưng subset đó phải là OUTPUT của SQL query, không phải raw CSV.

### C.2 Style Enforcement

Ở cell đầu tiên của MỌI notebook:
```python
import sys
sys.path.insert(0, '.')  # hoặc path tới module
from shadow_pnl_style import (
    apply_shadow_pnl_style, SHADOW_PNL_COLORS,
    format_vnd, format_pct, vnd_impact, init_audit_log,
    finalize_chart,
)
apply_shadow_pnl_style()
init_audit_log()
```

**Rules:**
- Chart color: CHỈ dùng từ `SHADOW_PNL_COLORS` dict — không hardcode hex
- Chart title: phải là câu INSIGHT (VD: "Streetwear chiếm 40% doanh thu nhưng chỉ 18% true margin"), KHÔNG mô tả data ("Revenue by Category")
- Mọi chart qua `finalize_chart()` để enforce consistency
- Mỗi chart save ra `outputs_round1/charts/{act}_{chart_name}.png` @ 300dpi

### C.3 VND Audit Discipline

**QUY TẮC #1 CỦA BÀI THI:** Không VND number nào được hardcode trong markdown nếu không có code compute nó.

```python
# ❌ SAI (lỗi v1 cũ)
# Trong markdown: "Impact: 460 tỷ VND"

# ✅ ĐÚNG
impact_vnd, impact_str = vnd_impact(
    label="Discount Curse — cohort-year LTV recovery",
    act="Act 3A",
    customers=27_171,
    rate=0.094,  # fraction, không phải percentage
    orders=4,
    aov_vnd=15_747,
    notebook="02_shadow_pnl_investigation.ipynb",
    note="AOV from SELECT MEDIAN(first_order_value) — see cell above",
)
print(f"Impact: {impact_str}")  # sẽ in "161 triệu VND"
```

`vnd_impact()` tự động:
1. Sanity check: fail nếu impact < 100K VND hoặc > 1000 tỷ VND (catches unit errors)
2. Log to `outputs_round1/shadow_pnl_audit.csv` — giám khảo verify được

### C.4 Anti-Leakage — Cho Act 4 Predictive

- Mọi lag feature: assert `train.max_date < val.min_date` với buffer ≥ 30 ngày
- Mọi rolling statistic: `shift(1)` trước khi rolling
- Mọi correlation test "X leads Y by N days": phải dùng OUT-OF-SAMPLE window, không full-series correlation

### C.5 MCQ Definition Consistency

Khi trong Act 3/4 cần tính metric đã xuất hiện ở MCQ, PHẢI dùng ĐÚNG definition từ `mcq_choice_answers.json`:

| Metric | Rule từ MCQ | Act cần |
|--------|-------------|---------|
| "order có discount" | `promo_id IS NOT NULL OR promo_id_2 IS NOT NULL` | Act 3A |
| "regional revenue" | EXCLUDE cancelled/returned statuses | Act 2, 3C |
| "cancelled orders" | orders.order_status = 'cancelled' (cross-check payments) | Act 3C |
| "return rate by size" | COUNT(returns) / COUNT(order_items), by RECORD | Act 3B |

### C.6 Checkpoint Protocol — STOP AFTER EACH ACT

**Mỗi Act xong, DỪNG LẠI và output cho user theo template:**

```
════════════════════════════════════════════════════════════════
✅ ACT [N] COMPLETED — [Act Name]
════════════════════════════════════════════════════════════════

📊 Charts produced:
    - outputs_round1/charts/act{N}_chart_1.png — [one-line description]
    - outputs_round1/charts/act{N}_chart_2.png — [...]

🔑 Key findings (số thật, không claim chưa verified):
    - [Finding 1 với số cụ thể từ SQL output]
    - [Finding 2]
    - [Finding 3]

💰 VND impact numbers (nếu có, từ audit log):
    - [Label]: [impact_str]  ← verify: outputs_round1/shadow_pnl_audit.csv row N

✅ DoD checklist:
    [✓/✗] DuckDB used for all aggregations
    [✓/✗] All colors from SHADOW_PNL_COLORS
    [✓/✗] All VND via format_vnd() or vnd_impact()
    [✓/✗] MCQ definitions consistent
    [✓/✗] Level coverage: Desc [✓/✗] Diag [✓/✗] Pred [✓/✗] Presc [✓/✗]
    [✓/✗] Multi-table: [list bảng dùng trong act này]

⚠️ Open questions / risks flagged for user review:
    - [Bất kỳ assumption nào chưa rõ]
    - [Data quality concerns]

🛑 STOPPING. Waiting for user "PROCEED" signal to start Act [N+1].
════════════════════════════════════════════════════════════════
```

**KHÔNG tự động start Act kế. Chờ user xác nhận.**

---

## PART D · EXECUTION PLAN — 5 ACTS DETAIL

### 📍 NOTEBOOK 1 — FOUNDATION (Acts 1 + 2)
File: `notebooks/01_shadow_pnl_foundation.ipynb`

---

### ACT 1 — THE ILLUSION

**Research question:**
> *Nhìn vào 10 năm dữ liệu, top-line của business này trông thế nào nếu chỉ tin báo cáo bề mặt?*

**Data needed:**
- `sales` (full 2012-2022)
- `orders`, `customers` (for counting)

**Charts required:**

**Chart 1.1 — Annual Revenue Growth**
- X: Year, Y: Total annual revenue
- Line + markers, color = `reported` (Deep Navy)
- Overlay COVID period (2020-Q2 → 2021-Q2) shaded region
- Title: *insight câu* về growth rate + COVID impact
- Annotation: CAGR 2012-2019 vs 2020-2022

**Chart 1.2 — Executive Dashboard Tile**
- 2x2 grid of KPI tiles hoặc horizontal bar summary:
  - Total Gross Revenue (10Y)
  - Total Orders
  - Total Unique Customers
  - Average Order Value (median)
- Tone: clean, minimal, "healthy business" feel

**Level coverage:**
- Descriptive (primary)
- Diagnostic setup (foreshadowing)

**The foreshadowing moment:**
Cuối Act 1 phải có 1 closing line dẫn sang Act 2:
> *"These numbers tell a story of growth. But we're asking: what do the OTHER 12 tables tell us about this same 10 years? Act 2 will peel back the layers."*

**DoD:**
- [ ] 2 charts produced, saved to `outputs_round1/charts/`
- [ ] All values via format_vnd()
- [ ] Style from apply_shadow_pnl_style()
- [ ] Narrative hook to Act 2 explicit

**Checkpoint:** STOP. Report. Wait for PROCEED.

---

### ACT 2 — THE UNMASKING (HERO CHART HERE)

**Research question:**
> *Từ mỗi 1,000 VND doanh thu báo cáo, thực sự bao nhiêu về bottom-line? Đâu là các "leaks"?*

**Data needed:**
- `sales` (reported gross)
- `order_items` (discount_amount sum)
- `returns` (refund_amount sum)
- `orders` + `shipments` (cancelled orders × shipping_fee)
- `inventory` + `web_traffic` (stockout phantom estimate)
- `products.cogs` (true COGS)

**SQL queries to build (team's SQL folder):**

```sql
-- 1. Gross revenue by year
SELECT EXTRACT(year FROM Date) AS year, SUM(Revenue) AS gross_revenue
FROM sales GROUP BY year ORDER BY year;

-- 2. Discount cost by year
SELECT EXTRACT(year FROM o.order_date) AS year,
       SUM(oi.discount_amount) AS discount_cost
FROM order_items oi JOIN orders o ON oi.order_id = o.order_id
GROUP BY year ORDER BY year;

-- 3. Return cost by year
SELECT EXTRACT(year FROM return_date) AS year,
       SUM(refund_amount) AS return_cost
FROM returns GROUP BY year ORDER BY year;

-- 4. Cancelled shipping absorbed
SELECT EXTRACT(year FROM o.order_date) AS year,
       SUM(s.shipping_fee) AS shipping_absorbed
FROM orders o JOIN shipments s ON o.order_id = s.order_id
WHERE o.order_status = 'cancelled' GROUP BY year;

-- 5. Stockout phantom (careful methodology — see note below)
-- Estimated lost revenue = stockout_days × avg_daily_demand × price
-- Với avg_daily_demand = units_sold / (days_in_month - stockout_days_clipped)
```

**⚠️ STOCKOUT PHANTOM METHODOLOGY NOTE:**
Đây là calculation nhạy cảm nhất. Phải document rõ assumptions:
1. `avg_daily_demand_if_no_stockout = units_sold / (days_in_month - stockout_days)`
2. `lost_units = avg_daily_demand × stockout_days`
3. `lost_revenue = lost_units × product.price`
4. Cap upper bound: assume max demand is 2x observed (tránh extrapolation crazy)
5. Flag rõ trong chart: "Phantom (estimated)" — khác với actual leaks

**Charts required:**

**Chart 2.1 — HERO WATERFALL (10-year accumulated)**
- X axis: categories in order [Gross, -Discount, -Return, -Cancelled Ship, -Stockout Phantom, =True Gross, -COGS, =True Net]
- Colors: Gross=`reported`, leaks=`leak_*` specific colors, True Gross=`true_net` at 50% alpha, True Net=`true_net` full
- Connecting lines dashed
- Annotations on EACH bar với VND amount (via format_vnd)
- Title: INSIGHT headline, VD: "Từ 1,234 tỷ VND doanh thu báo cáo, chỉ XX% về bottom-line"

**Chart 2.2 — Annual Leak Composition**
- Stacked bar per year (2012-2022)
- Bars = gross revenue, colored by leak breakdown + true remaining
- Shows: leak ratios đang growing/shrinking qua thời gian?

**Chart 2.3 — Leak Magnitude Summary Table (as chart)**
- Horizontal bar: each leak type với total 10Y cost
- Sorted descending
- Highlight top 2 leaks — these become Act 3 focus

**Level coverage:**
- Descriptive (magnitude quantification)
- Diagnostic beginning (hierarchy of leaks)

**DoD:**
- [ ] Waterfall chart VND all traced to SQL (audit CSV entries created)
- [ ] Stockout phantom methodology documented in markdown cell
- [ ] Top 2 leaks identified → these drive Act 3 priorities
- [ ] Hero chart polished (this is the showpiece — extra care)

**Checkpoint:** This is the most important chart of entire report. STOP, report in detail. Wait for explicit PROCEED.

---

### 📍 NOTEBOOK 2 — INVESTIGATION (Acts 3 + 4 + 5)
File: `notebooks/02_shadow_pnl_investigation.ipynb`

---

### ACT 3 — THE PERPS (Forensic Breakdown)

**4 sub-acts, each is a mini forensic investigation.**
Sub-act 3A-3D order can be rearranged based on top leaks from Act 2.

#### ACT 3A — The Discount Trap
**Question:** *Discount type × category × season nào đang destroy margin?*

- 3D matrix analysis: promo_type × applicable_category × season
- Stratified analysis by `first_order_value` quintile (KILL selection bias)
- Optional: Propensity Score Matching nếu có bandwidth
- Chart: Heatmap (promo_type × category) với cell color = true margin contribution

**Integrates:** Legacy "Welcome Discount Curse" work được absorbed — NOT abandoned.

#### ACT 3B — The Return Bleeding
**Question:** *Size × category combination nào đang burn refund? Có predict được từ reviews không?*

- Return rate heatmap: size × category (từ MCQ Q9 → highlight S = top)
- Return reason breakdown cho worst cell
- Reviews as leading indicator: logistic regression rating → P(return)
- Chart: Heatmap + secondary chart reviews-to-return correlation

#### ACT 3C — The Cancellation Vortex
**Question:** *Credit card dẫn đầu cancelled orders (MCQ Q8) — WHY và cost bao nhiêu?*

- Cancellation rate by payment method
- Installments distribution in cancelled CC orders (fraud vs auth-fail vs remorse hypothesis)
- Order value distribution: CC cancelled vs others
- Time-to-cancel analysis (if shipments data allows)

#### ACT 3D — The Stockout Phantom
**Question:** *Khi product stockout, web_traffic vẫn show demand — bao nhiêu doanh thu thực sự mất?*

- Monthly stockout by category
- Join với web_traffic same-period to quantify unmet demand
- Top 10 SKUs with highest phantom revenue loss

**Level coverage for Act 3 overall:**
- Diagnostic (primary)
- Some Predictive (logistic regression in 3B, leading indicator in 3D)

**DoD:**
- [ ] 4 sub-acts completed (or 3 if team decides to cut one, must justify)
- [ ] Each sub-act has ≥1 chart
- [ ] VND impact quantified for each leak type
- [ ] Specific culprits named (SKUs, segments, patterns)

**Checkpoint after EACH sub-act** (3A stop, 3B stop, ...) — 4 mini-checkpoints.

---

### ACT 4 — THE TRAJECTORY

**Research question:**
> *Nếu không fix các leaks này, 2023 sẽ thế nào? Leading indicators nào early-warn?*

**Charts required:**

**Chart 4.1 — True Margin Trajectory Forecast**
- X: Year (2012-2023), Y: True margin %
- 2 scenarios plotted for 2023:
  - Status quo (leak ratios continue trend)
  - Intervention (leaks cut by Act 5 recommendations)
- Uncertainty band

**Chart 4.2 — Leading Indicators Panel**
- 4 subplot panel:
  - Monthly return rate trend (30d MA)
  - Average review rating trend (30d MA)
  - Cancellation rate trend (30d MA)
  - Web-to-revenue lag correlation
- Mark anomalies, forecast next 6 months

**Chart 4.3 — Feature Bridge to Part 3 (Forecasting)**
- List of features discovered in Acts 3-4 that will feed LightGBM/Prophet pipeline
- Export to `outputs_round1/features_for_part3.csv`:
  ```
  feature_name, data_source, lag_days, act_discovered, expected_importance
  return_rate_roll30_lag7, returns+order_items, 7, 4, HIGH
  review_rating_shift30_lag14, reviews, 14, 3B, MEDIUM
  ...
  ```

**Level coverage:**
- Predictive (primary)
- Diagnostic (anomaly detection)

**Anti-leakage assertions:**
```python
# Trong mọi time series analysis
assert forecast_train.max_date + pd.Timedelta(days=30) < forecast_val.min_date, \
    f"Leakage detected: train ends {forecast_train.max_date}, val starts {forecast_val.min_date}"
```

**DoD:**
- [ ] 3 charts produced
- [ ] Feature bridge CSV exported
- [ ] Anti-leakage assertions pass
- [ ] Forecast scenarios documented with assumptions

**Checkpoint.** STOP.

---

### ACT 5 — THE SCALPEL

**Research question:**
> *3 actions cụ thể, prioritized, quantified. Cái nào lớn nhất impact với smallest risk?*

**Chart 5.1 — 3-Wave Surgical Plan (Infographic)**
```
WAVE 1 (Week 1-4): [Action tied to Act 3 top leak]
    VND recovery: [from vnd_impact()]
    Confidence: High/Medium/Low
    Implementation effort: [hours/days]

WAVE 2 (Month 2-3): [Second priority]
    ...

WAVE 3 (Quarter 2): [Third, higher-risk/higher-reward]
    ...

TOTAL OPPORTUNITY: [sum VND] / year
vs CURRENT LEAK (from Act 2): [leak VND] / year
RECOVERY RATIO: X%
```

**Chart 5.2 — Risk-Reward Matrix**
- 2x2 quadrant
- X: Implementation effort
- Y: VND recovery expected
- Plot each recommendation as bubble (size = confidence)

**Chart 5.3 — Trade-off Analysis (Optional)**
- For top recommendation: scenario table
  - Conservative / Base / Optimistic outcomes
  - Break-even timeline
  - What could go wrong

**Level coverage:**
- Prescriptive (primary)
- Everything else referenced

**DoD:**
- [ ] 3 waves defined với VND từ audit trail
- [ ] Each wave ties back to specific Act 3 finding
- [ ] Timeline + priority explicit
- [ ] "What could go wrong" documented (honest risk disclosure)

**Final checkpoint.** STOP. Produce executive summary. User reviews full package before report writing.

---

## PART E · FILE STRUCTURE & DELIVERABLES

```
project_root/
├── notebooks/
│   ├── 01_shadow_pnl_foundation.ipynb       # Acts 1 + 2
│   └── 02_shadow_pnl_investigation.ipynb    # Acts 3 + 4 + 5
│
├── shadow_pnl_style.py                       # utility module
│
├── sql/
│   ├── act2_waterfall_gross.sql
│   ├── act2_waterfall_discount.sql
│   ├── act2_waterfall_return.sql
│   ├── act2_waterfall_shipping.sql
│   ├── act2_waterfall_stockout.sql
│   ├── act3a_discount_trap.sql
│   ├── act3b_return_bleeding.sql
│   ├── act3c_cancellation_vortex.sql
│   └── act3d_stockout_phantom.sql
│
└── outputs_round1/
    ├── charts/
    │   ├── act1_revenue_growth.png
    │   ├── act1_executive_dashboard.png
    │   ├── act2_waterfall_hero.png          # HERO CHART
    │   ├── act2_annual_composition.png
    │   ├── act2_leak_magnitude.png
    │   ├── act3a_discount_trap_matrix.png
    │   ├── act3b_return_heatmap.png
    │   ├── act3c_cancellation_forensics.png
    │   ├── act3d_stockout_phantom.png
    │   ├── act4_margin_trajectory.png
    │   ├── act4_leading_indicators.png
    │   ├── act5_surgical_plan.png
    │   └── act5_risk_reward_matrix.png
    │
    ├── shadow_pnl_audit.csv                 # VND audit trail (submission)
    └── features_for_part3.csv               # Bridge to forecasting
```

---

## PART F · ANTI-PATTERNS (Lỗi v1 KHÔNG được lặp lại)

Kiểm tra lại list này TRƯỚC khi mỗi Act hoàn tất:

| # | Lỗi v1 | Prevention in v2 |
|---|--------|-------------------|
| 1 | Hardcode VND "460 tỷ" trong markdown, số thật chỉ "0.2 tỷ" | Mọi VND qua `format_vnd()` hoặc `vnd_impact()` — audit CSV verify được |
| 2 | Unit error: confuse `triệu` với `tỷ` (1000x) | `vnd_impact()` sanity check range 1e5-1e12 |
| 3 | Claim "causation" từ observational data | Từ "associated with", "correlated", ngoại trừ PSM/DiD sections có methodology |
| 4 | Bỏ qua confound `first_order_value` | Stratified analysis quintile bắt buộc trong Act 3A |
| 5 | Narrative contradicts SQL output | Mọi số trong markdown phải xuất phát từ biến Python compute trong cell trước |
| 6 | Định nghĩa metric không khớp MCQ answers | Use rules trong C.5 strict |
| 7 | "Predictive" chỉ là phép nhân số học | Act 4 phải có time-aware split + leading indicator analysis real |
| 8 | Load tất cả CSV bulk vào Pandas | DuckDB-first policy (C.1) |
| 9 | Chart title mô tả data thay vì insight | `finalize_chart()` nhắc, reviewer check khi checkpoint |
| 10 | Bỏ qua non-monotonic pattern để fit narrative | Truth Serum: nếu data non-monotonic, report honestly, investigate why |

---

## PART G · START SIGNAL

Khi bạn đã:
1. Đọc xong các file Part A.1
2. Confirmed 4 points in A.2
3. Imported and tested `shadow_pnl_style.py`

Output đúng message sau và CHỜ user reply "GO ACT 1":

```
╔════════════════════════════════════════════════════════════════╗
║ SHADOW P&L MISSION — CONTEXT LOADED                            ║
╠════════════════════════════════════════════════════════════════╣
║ ✓ Read: PROJECT_BASED_KNOWLEDGE, DATATHON strategy, exam PDF   ║
║ ✓ Read: schema, warehouse.py, audit_summary, mcq_answers       ║
║ ✓ Confirmed: 4 Levels rubric, DuckDB policy, MCQ rules, VND    ║
║ ✓ shadow_pnl_style.py imported, self-test passed               ║
║                                                                ║
║ Ready to start ACT 1 — THE ILLUSION.                           ║
║                                                                ║
║ Notebook will be: notebooks/01_shadow_pnl_foundation.ipynb     ║
║ Will STOP and checkpoint after Act 1 before starting Act 2.    ║
║                                                                ║
║ Awaiting user signal: "GO ACT 1"                               ║
╚════════════════════════════════════════════════════════════════╝
```

---

## APPENDIX · ESCALATION PROTOCOL

Nếu gặp tình huống sau, DỪNG và HỎI user, không tự quyết:

1. **Data quality issue nghiêm trọng** không có trong `audit_summary.csv`
2. **SQL query timeout** (> 2 phút) → user có muốn optimize hay chạy trên subset?
3. **Finding contradicts expected narrative** (VD: discount thực ra không phải top leak) → report honestly, ask user về pivot
4. **VND sanity check fails** repeatedly → có thể assumption sai fundamental, cần user review
5. **Disagreement with MCQ answer** — nếu Act 3 compute ra metric khác MCQ → flag ngay, không tự override

Honesty > narrative. Team thà có bài honestly thấp hơn là bài high với numbers fabricated.

---

*Brief Version: 1.0 · Generated by Grandmaster Data Co-Pilot*
*Team: DATATHON 2026 Gridbreakers · Target: Top 3*
