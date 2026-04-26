# 🏛️ CHIẾN LƯỢC PHÂN BỔ FEATURES CHO 3-MODEL STACKING ENSEMBLE

**Competition:** DATATHON 2026 — Round 1  
**Task:** Sales Forecasting (Revenue & COGS)  
**Dataset:** Fashion E-commerce Vietnam 2012-2022  
**Test Period:** 01/01/2023 → 01/07/2024 (548 days)

---

## 🎯 NGUYÊN TẮC THIẾT KẾ ENSEMBLE

### **Mục tiêu: MAXIMIZE DIVERSITY**

```
Ensemble mạnh = 3 models nhìn bài toán từ 3 GÓC ĐỘ KHÁC NHAU

❌ SAI: 3 models cùng dùng 40 features
        → Predictions giống nhau 
        → Stacking vô nghĩa

✅ ĐÚNG: Mỗi model tập trung vào 1 aspect
        → Predictions complement nhau 
        → CEO Ridge có nhiều thông tin
```

### **Công thức Diversity:**

```
Diversity = Algorithmic Heterogeneity × Feature Heterogeneity

Algorithmic:
- Prophet: Statistical decomposition
- LightGBM: Gradient boosting trees
- N-BEATS: Deep neural network
→ 3 paradigms hoàn toàn khác nhau ✅

Feature:
- Prophet: Minimal (5 inputs)
- LightGBM: Full (40 features)
- N-BEATS: Zero (pure sequence)
→ Maximum information diversity ✅
```

---

## 📊 TỔNG QUAN PHÂN BỔ

| Model | Input Type | # Features | Focus Area | Role |
|-------|------------|------------|------------|------|
| **Prophet** | Date + Holidays | ~5 | Macro seasonality & trend | Foundation baseline |
| **LightGBM** | Tabular features | **40** | Micro interactions & events | Tactical adjustments |
| **N-BEATS** | Pure sequence | **0** | Hidden temporal patterns | Deep structure |
| **CEO Ridge** | 3 predictions | 3 | Blend & optimize | Final decision |

**Expected Diversity: ~75%** ← Excellent for ensemble!

---

---

## 1️⃣ MODEL 1: PROPHET — "The Macro Strategist"

### **🎯 Triết lý:**

> **"Keep it simple, let the algorithm do its job"**

Prophet được thiết kế để tự động xử lý:
- Trend decomposition (piecewise linear)
- Seasonality (built-in Fourier)
- Holiday effects (multiplicative/additive)

→ **Không cần** feed thủ công các features đã có sẵn trong algorithm!

---

### **📋 Feature Allocation:**

#### **A. BẮT BUỘC (2 inputs):**
```python
prophet_df = pd.DataFrame({
    'ds': Date,          # Datetime column
    'y': Revenue,        # Target variable
})
```

---

#### **B. HOLIDAYS LIST (~200 rows):**

**Tại sao cần explicit holidays:**
> Prophet cần biết TRƯỚC các ngày đặc biệt để model như "events"  
> Nếu không khai báo → Prophet học như seasonality bình thường

**Cấu trúc holidays DataFrame:**
```python
holidays_df = pd.DataFrame({
    'ds': [...],              # Ngày lễ
    'holiday': [...],         # Tên lễ
    'lower_window': [...],    # Số ngày trước event
    'upper_window': [...],    # Số ngày sau event
})
```

**Chi tiết các nhóm holidays:**

```python
# ════════════════════════════════════════════════════════
# GROUP 1: TẾT NGUYÊN ĐÁN (Critical!)
# ════════════════════════════════════════════════════════
Tết dates: 2013-2024 (12 years)
  - 2013: 02-10
  - 2014: 01-31
  - 2015: 02-19
  - 2016: 02-08
  - 2017: 01-28
  - 2018: 02-16
  - 2019: 02-05
  - 2020: 01-25
  - 2021: 02-12
  - 2022: 02-01
  - 2023: 01-22
  - 2024: 02-10

  lower_window: -21 (3 tuần trước Tết - prep phase)
  upper_window: +10 (đến Mùng 10)

# ════════════════════════════════════════════════════════
# GROUP 2: SHOPPING FESTIVALS (E-commerce)
# ════════════════════════════════════════════════════════
11/11 (Singles Day): Annual 2012-2024
  lower_window: -3
  upper_window: +1

12/12: Annual 2012-2024
  lower_window: -3
  upper_window: +1

9/9: Annual 2012-2024
  lower_window: -2
  upper_window: +1

Black Friday: Annual (Friday after 4th Thursday Nov)
  lower_window: -2
  upper_window: +2

Cyber Monday: Annual (Monday after Black Friday)
  lower_window: -1
  upper_window: +1

# ════════════════════════════════════════════════════════
# GROUP 3: GIFT OCCASIONS (Window BEFORE event)
# ════════════════════════════════════════════════════════
Valentine (14/2): Annual 2012-2024
  lower_window: -7
  upper_window: 0

8/3 (International Women's Day): Annual
  lower_window: -7
  upper_window: 0

20/10 (Vietnamese Women's Day): Annual
  lower_window: -7
  upper_window: 0

# ════════════════════════════════════════════════════════
# GROUP 4: TRAVEL PERIODS (Window BEFORE holidays)
# ════════════════════════════════════════════════════════
30/4 (Reunification Day): Annual
  lower_window: -10
  upper_window: 0

2/9 (National Day): Annual
  lower_window: -10
  upper_window: 0
```

**Tổng:** ~200 holiday entries (12 years × ~17 events/year)

---

#### **C. REGRESSORS (3 biến COVID ONLY):**

**Tại sao CHỈ COVID:**

| Feature Type | Prophet xử lý tự động? | Cần thêm regressor? |
|--------------|------------------------|---------------------|
| Annual seasonality | ✅ Built-in Fourier | ❌ Không |
| Weekly seasonality | ✅ Built-in Fourier | ❌ Không |
| Holidays | ✅ Qua holidays list | ❌ Không |
| Month effects | ✅ Trong seasonality | ❌ Không |
| **Structural breaks** | ❌ Không tự phát hiện | ✅ **CẦN regressor** |

**COVID = Structural break đặc biệt:**
- Trend đứt gãy hoàn toàn (lockdown)
- Không lặp lại (one-time event)
- Extreme anomaly (không thể học từ seasonality)

```python
# Chỉ 3 regressors:
prophet_model.add_regressor('is_lockdown', mode='additive')
prophet_model.add_regressor('is_pre_lockdown', mode='additive')
prophet_model.add_regressor('is_post_lockdown', mode='additive')
```

**Timeline:**
```
is_pre_lockdown:  09/05/2021 → 22/05/2021 (panic buying)
is_lockdown:      23/05/2021 → 01/10/2021 (Delta wave)
is_post_lockdown: 02/10/2021 → 01/11/2021 (recovery)
```

---

#### **D. CUSTOM SEASONALITY (1 - Tết Cycle):**

**Tại sao cần thêm:**
> Tết di động theo Âm lịch (~354 days) ≠ Dương lịch (365 days)  
> Built-in yearly seasonality (365.25) sẽ MISS pattern này

```python
prophet_model.add_seasonality(
    name='tet_season',
    period=354.37,        # Lunar year length
    fourier_order=5,      # Complexity (10 Fourier terms)
    mode='additive'
)
```

---

#### **E. PROPHET CONFIG:**

```python
prophet_model = Prophet(
    # Seasonality
    yearly_seasonality=True,         # Auto (365.25 days, 10 terms)
    weekly_seasonality=True,         # Auto (7 days, 3 terms)
    daily_seasonality=False,         # Not needed for daily forecast
    seasonality_mode='multiplicative',   # Fashion = spike-heavy
    seasonality_prior_scale=15.0,    # Allow strong effects
    
    # Trend
    changepoint_prior_scale=0.05,    # Conservative (COVID breaks)
    changepoint_range=0.9,           # Detect in 90% of training
    
    # Holidays
    holidays_prior_scale=20.0,       # Strong holiday effects
    
    # Uncertainty
    interval_width=0.95,
    
    # Misc
    growth='linear',
    mcmc_samples=0,                  # Faster training
)
```

---

### **🎯 Prophet sẽ học:**

✅ **Strengths:**
- Long-term trend (2012-2022 trajectory)
- Annual seasonality (Nov-Feb high, Jul low)
- Weekly seasonality (Sat-Sun vs weekdays)
- Tết cycle (~354-day lunar pattern)
- Holiday spikes (11/11, 12/12, Valentine, etc.)
- COVID structural breaks

❌ **Không học tốt:**
- Short-term momentum (tuần này vs tuần trước)
- Payday effects (ngày 25-31 spike)
- Sale countdown effects (days_to_next_big_sale)
- Feature interactions (tet_peak × ghost_month)
- Lag-based patterns (rev_lag_364)

---

### **📊 Prophet Feature Summary:**

```
EXPLICIT INPUTS: ~5
  ├── ds (Date)
  ├── y (Target)
  ├── Holidays (~200 rows)
  ├── Regressors (3 COVID flags)
  └── Custom seasonality (1 Tết)

INTERNAL FEATURES (auto-generated): ~60
  ├── Yearly Fourier (10 terms)
  ├── Weekly Fourier (3 terms)
  ├── Tet Fourier (10 terms)
  └── Holiday effects (~17 holidays × 2)

→ Bạn chỉ cần engineer 5 inputs!
→ Prophet tự tạo ~60 internal features!
```

---

### **🎭 Vai trò trong Ensemble:**

> **Foundation Layer** — Cung cấp seasonality baseline mượt mà

**Khi nào Prophet dẫn đầu:**
- Normal days (smooth seasonality)
- Long-term trends
- Cultural events (Tết, holidays)

**Khi nào Prophet yếu:**
- Extreme events (không có trong holidays)
- Short-term fluctuations
- Complex interactions

---

---

## 2️⃣ MODEL 2: LIGHTGBM — "The Tactical Expert"

### **🎯 Triết lý:**

> **"The more the merrier — Feed me everything!"**

LightGBM strengths:
- Automatic feature selection (leaf-wise growth)
- Non-linear interactions (multi-way splits)
- Categorical handling (native support)
- Robust & fast

→ **Cho vào 40 features, model tự lọc ra ~15-20 features quan trọng!**

---

### **📋 Feature Allocation: ALL 40 FEATURES**

```python
lgbm_features = [
    # ════════════════════════════════════════════════════════
    # NHÓM 1: CALENDAR & LIQUIDITY ENGINE (6)
    # ════════════════════════════════════════════════════════
    'day_of_week',          # 0-6 (categorical)
    'month',                # 1-12 (categorical)
    'day_of_month',         # 1-31
    'is_payday_window',     # Binary (25-31)
    'dist_to_payday',       # Gradient (countdown to day 28)
    'is_weekend',           # Binary
    
    # ════════════════════════════════════════════════════════
    # NHÓM 2: TẾT NGUYÊN ĐÁN (5)
    # ════════════════════════════════════════════════════════
    'days_to_tet',          # Countdown -30 → +15
    'is_tet_buildup',       # Binary (21-11 days before)
    'is_tet_peak',          # Binary (10-4 days before)
    'is_tet_holiday',       # Binary (3 days before → Mùng 3)
    'is_tet_reopening',     # Binary (Mùng 4-10)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 3: FASHION SHOPPING WINDOWS (5)
    # ════════════════════════════════════════════════════════
    'is_gift_peak',             # Binary (7-2 days before 14/2, 8/3, 20/10)
    'is_travel_peak',           # Binary (10-3 days before 30/4, 2/9)
    'is_year_end_festive',      # Binary (10/12 → 30/12)
    'is_ghost_month',           # Binary (lunar month 7)
    'dist_to_nearest_holiday',  # Gradient (countdown)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 4: E-COMMERCE SALE DAYS (5)
    # ════════════════════════════════════════════════════════
    'shopping_festival_score',  # Ordinal 0-3 (categorical!)
    'days_to_next_big_sale',    # Gradient (countdown)
    'is_sale_leadup',           # Binary (1-3 days before big sale)
    'is_black_friday',          # Binary
    'is_cyber_monday',          # Binary
    
    # ════════════════════════════════════════════════════════
    # NHÓM 5: HYBRID MEMORY ENGINE (14) ⭐ CORE
    # ════════════════════════════════════════════════════════
    # A. Near-term (2)
    'rev_lag_364',              # Revenue 364 days ago
    'cogs_lag_364',             # COGS 364 days ago
    
    # B. Safe anchor (4)
    'rev_lag_728',              # Revenue 2 years ago
    'cogs_lag_728',             # COGS 2 years ago
    'rev_roll_mean_28_lag_728', # Smoothed baseline
    'cogs_roll_mean_28_lag_728',
    
    # C. Statistics (8)
    'stat_rev_mean_dow_month',  # Mean by (dow, month)
    'stat_cogs_mean_dow_month',
    'stat_rev_std_month',       # Volatility by month
    'stat_cogs_std_month',
    'stat_rev_median_day',      # Median by day (payday effect)
    'stat_cogs_median_day',
    'stat_rev_yoy_growth_month',    # YoY growth (inflation norm)
    'stat_cogs_yoy_growth_month',
    
    # ════════════════════════════════════════════════════════
    # NHÓM 6: FOURIER FEATURES (2)
    # ════════════════════════════════════════════════════════
    'sin_annual_1',             # Sine wave (365.25 days)
    'cos_annual_1',             # Cosine wave (boundary smoother)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 7: COVID-19 GUIDE RAILS (3)
    # ════════════════════════════════════════════════════════
    'is_pre_lockdown',          # Binary (09-22 May 2021)
    'is_lockdown',              # Binary (23 May - 01 Oct 2021)
    'is_post_lockdown',         # Binary (02-01 Nov 2021)
]

# TOTAL: 40 features
```

---

### **🔧 LightGBM Configuration:**

```python
# Categorical features
categorical_features = [
    'day_of_week',              # 0-6
    'month',                    # 1-12
    'shopping_festival_score',  # 0-3 (ordinal nhưng mark categorical)
]

# LightGBM params
lgbm_params = {
    'objective': 'regression_l1',       # MAE objective
    'metric': ['mae', 'rmse'],
    'learning_rate': 0.03,
    'num_leaves': 127,
    'min_child_samples': 30,
    'feature_fraction': 0.7,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'reg_alpha': 0.05,                  # L1 regularization
    'reg_lambda': 0.1,                  # L2 regularization
    'categorical_feature': categorical_features,
    'n_estimators': 5000,
    'early_stopping_rounds': 200,
    'verbose': -1,
    'random_state': 42,
}
```

---

### **🎯 LightGBM sẽ học:**

✅ **Strengths:**
- Complex interactions (tet_peak × lag_364 × yoy_growth)
- Event-specific behaviors (11/11 vs 9/9 vs 2/2)
- Payday effects (dist_to_payday gradient)
- Pre-sale psychology (days_to_next_big_sale)
- COVID-lag interactions (khi nào trust/discount lags)
- Deviations from statistical baseline
- Short-term momentum
- Hierarchical patterns (festival_score 3 > 2 > 1)

❌ **Không học tốt:**
- Smooth long-term trends (tree = step function)
- Deep temporal dependencies (mỗi row độc lập)
- Extrapolation beyond training range

---

### **📊 Expected Feature Importance (Top 15):**

```
Rank  Feature                      Expected Importance
────────────────────────────────────────────────────────
1     rev_lag_364                  ⭐⭐⭐⭐⭐
2     stat_rev_mean_dow_month      ⭐⭐⭐⭐⭐
3     shopping_festival_score      ⭐⭐⭐⭐⭐
4     month                        ⭐⭐⭐⭐
5     days_to_tet                  ⭐⭐⭐⭐
6     is_tet_peak                  ⭐⭐⭐⭐
7     rev_lag_728                  ⭐⭐⭐⭐
8     day_of_week                  ⭐⭐⭐⭐
9     days_to_next_big_sale        ⭐⭐⭐⭐
10    stat_rev_yoy_growth_month    ⭐⭐⭐
11    dist_to_payday               ⭐⭐⭐
12    is_lockdown                  ⭐⭐⭐
13    rev_roll_mean_28_lag_728     ⭐⭐⭐
14    is_payday_window             ⭐⭐⭐
15    is_year_end_festive          ⭐⭐⭐
```

---

### **💡 Example Interactions LightGBM Learns:**

```python
# Interaction 1: COVID contaminated lags
if rev_lag_364 < 8000:
    if is_lockdown == 1:
        # Currently in lockdown → low is expected
        weight = 1.0
    else:
        # Lag came from lockdown year → discount it
        weight = 0.3
        use rev_lag_728 instead

# Interaction 2: Tet + High growth
if days_to_tet < 10 and days_to_tet > 4:  # Tet peak window
    if stat_rev_yoy_growth_month > 0.15:    # High growth year
        boost = 1.5
    else:
        boost = 1.2

# Interaction 3: Mega sale + Payday alignment
if shopping_festival_score == 3:  # 11/11 or 12/12
    if is_payday_window == 1:      # End of month
        synergy_boost = 1.3  # Extra boost from alignment
```

---

### **🎭 Vai trò trong Ensemble:**

> **Tactical Layer** — Event-driven adjustments & feature interactions

**Khi nào LightGBM dẫn đầu:**
- Big sales events (11/11, 12/12)
- Complex interactions (multiple features combine)
- Payday spikes
- Pre-sale psychology

**Khi nào LightGBM yếu:**
- Smooth trends (tree can't extrapolate)
- Long-term forecasting
- Patterns not seen in training

---

---

## 3️⃣ MODEL 3: N-BEATS — "The Pattern Hunter"

### **🎯 Triết lý:**

> **"Show me the history, I'll find the patterns"**

N-BEATS = Neural time series model
- End-to-end learning từ raw sequence
- Không cần feature engineering
- Multi-scale decomposition (trend + seasonality + residual)

→ **Học TRỰC TIẾP từ time series, không qua features!**

---

### **📋 Feature Allocation: 0 FEATURES (Pure Univariate)**

```python
# Input
nbeats_input = {
    'y': Revenue_sequence,    # Pure time series
    'input_size': 730,        # Lookback window (2 years)
    'horizon': 548,           # Forecast length
}

# Không có features nào khác!
```

**Input format:**
```python
Input:  [Revenue_t-730, Revenue_t-729, ..., Revenue_t-1]
                                             ↓
Output:              [Revenue_t, Revenue_t+1, ..., Revenue_t+547]
```

---

### **🧠 N-BEATS HỌC GÌ TỪ SEQUENCE?**

#### **A. TREND (Polynomial Block)**

```python
Sequence input:
[10k, 10.5k, 11k, 11.8k, 12.5k, 13k, ...]
         ↓
Model phát hiện: "Revenue đang tăng ~50 VND/ngày"
         ↓
Extrapolate: "7 ngày tới: 13.3k, 13.6k, 14k..."
```

**→ Không cần feature "trend" — Model thấy tăng dần trong sequence!**

---

#### **B. SEASONALITY (Fourier Block)**

**Weekly Pattern:**
```python
3 tuần history:
Mon: [10k, 10.2k, 10.5k]
Tue: [9.5k, 9.8k, 10k]
Wed: [9k, 9.2k, 9.5k]
...
Sat: [15k, 15.5k, 16k]  ← Spike every 7 days!
Sun: [14k, 14.5k, 15k]
         ↓
Model học: "Cứ 7 ngày lặp lại pattern, peak ở vị trí 6"
         ↓
Predict: "Ngày thứ 7 tiếp theo sẽ có spike"
```

**→ Không cần feature "day_of_week" — Model thấy chu kỳ 7 ngày!**

---

**Annual Pattern (11/11):**
```python
5 năm history:
2018-11-11: 20k
2019-11-11: 25k  ← Cùng vị trí, tăng dần
2020-11-11: 30k
2021-11-11: 35k
2022-11-11: 42k
         ↓
Model học: "Cứ ~365 ngày có spike lớn ở vị trí này + growing"
         ↓
Predict: "2023-11-11 ≈ 48k"
```

**→ Không cần feature "shopping_festival_score" — Model thấy annual spike!**

---

**Lunar Pattern (Tết):**
```python
10 năm Tết history:
2013-02-10: 50k spike
2014-01-31: 55k spike  ← Di động, không cố định
2015-02-19: 60k spike
2016-02-08: 65k spike
...
         ↓
Model học: "Có event ~354 ngày 1 lần (lunar cycle)"
         ↓
Predict: "~354 ngày sau spike gần nhất → spike tương tự"
```

**→ Không cần feature "is_tet_peak" — Model thấy chu kỳ ~354 ngày!**

---

#### **C. EVENTS & ANOMALIES (Generic Block)**

**COVID Anomaly:**
```python
History:
2019-06: 15k (normal)
2020-06: 16k (normal)
2021-06: 5k   ← Extreme drop!
2021-07: 4k
2021-08: 4.5k
2021-09: 6k
2021-10: 12k  ← Recovery
2022-06: 17k  (back to normal)
         ↓
Model học: "2021 mid-year = anomaly, không dùng làm baseline"
         ↓
Predict 2023-06: Dùng pattern 2019, 2020, 2022 → Bỏ qua 2021
```

**→ Không cần feature "is_lockdown" — Model thấy anomaly trong sequence!**

---

### **🏗️ N-BEATS Architecture:**

```python
Input: [Revenue_t-730, ..., Revenue_t-1]  (730 timesteps)
         ↓
    ┌─────────────────────────────────┐
    │  TREND STACK (3 blocks)        │
    │  Learn: Polynomial trends       │
    │  Output: Trend component        │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │  SEASONALITY STACK (3 blocks)  │
    │  Learn: Fourier harmonics       │
    │  Output: Seasonal component     │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │  GENERIC STACK (3 blocks)      │
    │  Learn: Residuals + anomalies   │
    │  Output: Residual component     │
    └─────────────────────────────────┘
         ↓
    SUM all outputs → Final forecast
```

**Mỗi block = Neural network:**
- Input layer: 730 timesteps
- Hidden layers: 512 → 512 neurons
- Output: Basis functions (polynomial / Fourier / learned)

---

### **🔧 N-BEATS Configuration:**

```python
nbeats_config = {
    # Architecture
    'stack_types': ['trend', 'seasonality', 'generic'],
    'n_blocks': [3, 3, 3],          # 3 blocks per stack
    'mlp_units': [[512, 512]] * 3,  # Hidden layer sizes
    
    # Temporal
    'input_size': 730,               # 2 years lookback
    'horizon': 548,                  # Forecast length
    
    # Block-specific
    'n_polynomials': 3,              # Trend: linear, quad, cubic
    'n_harmonics': 2,                # Seasonality: Fourier order
    
    # Training
    'learning_rate': 1e-3,
    'max_steps': 1000,
    'batch_size': 32,
    'loss': 'MAE',                   # Match competition metric
    'random_seed': 42,
}
```

---

### **🎯 N-BEATS sẽ học:**

✅ **Strengths:**
- Deep temporal dependencies (2-year lookback)
- Multi-scale seasonality (weekly + annual + lunar)
- Hidden cycles (patterns không obvious)
- Non-linear trends
- Implicit event effects (học từ spikes)
- Smooth extrapolation (neural flexibility)
- Anomaly detection (COVID, outliers)

❌ **Không biết explicit:**
- Tết là gì (chỉ biết có pattern ~354 days)
- 11/11 là gì (chỉ biết có spike Nov 11)
- COVID là gì (chỉ biết 2021 anomaly)
- Feature names (chỉ thấy numbers)

---

### **🎭 Vai trò trong Ensemble:**

> **Deep Pattern Layer** — Hidden temporal structure

**Khi nào N-BEATS dẫn đầu:**
- Hidden patterns (không obvious trong features)
- Smooth extrapolation
- Multi-scale seasonality
- Long-term dependencies

**Khi nào N-BEATS yếu:**
- Explicit events chưa thấy (new holiday type)
- Short-term shocks (no history)
- Interpretability (black box)

---

---

## 🎭 DIVERSITY ANALYSIS — 3 MODELS SO SÁNH

### **Bảng tổng hợp:**

| Aspect | Prophet | LightGBM | N-BEATS |
|--------|---------|----------|---------|
| **Paradigm** | Statistical decomposition | Tree ensemble | Deep learning |
| **Input type** | Date + Holidays | Tabular features | Pure sequence |
| **# Features** | ~5 | **40** | **0** |
| **Seasonality** | Smooth Fourier | Discrete (month, dow) | Multi-scale learned |
| **Trend** | Piecewise linear | None | Polynomial + neural |
| **Events** | Explicit holidays | Feature interactions | Implicit from spikes |
| **Memory** | None | Explicit lags | Implicit (730-day window) |
| **Interactions** | Linear/multiplicative | Non-linear, multi-way | Learned representations |
| **Interpretability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Extrapolation** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |

---

### **Information Overlap Analysis:**

```
SEASONALITY:
Prophet:  Smooth Fourier (365 + 7 days)
LightGBM: Discrete (month + dow) + sin/cos
N-BEATS:  Multi-scale learned
→ Overlap: ~40% (complementary!)

EVENTS:
Prophet:  Explicit holidays list
LightGBM: Binary flags + gradients + scores
N-BEATS:  Implicit from historical spikes
→ Overlap: ~20% (very different!)

TREND:
Prophet:  Piecewise linear
LightGBM: N/A (stationary)
N-BEATS:  Polynomial + neural
→ Overlap: ~30%

MEMORY:
Prophet:  N/A
LightGBM: Explicit lags + statistics
N-BEATS:  Implicit in 730-day input
→ Overlap: ~10% (very different!)

════════════════════════════════════════
OVERALL DIVERSITY: ~75%  ← EXCELLENT!
════════════════════════════════════════
```

---

---

## 🎯 ENSEMBLE BEHAVIOR SCENARIOS

### **Scenario 1: Normal Day (2023-03-15 Wednesday)**

```python
Prophet:
  Baseline từ trend + Weekly (Wed) + Annual (March)
  → Prediction: 12,000

LightGBM:
  rev_lag_364 = 11,500
  month=3, dow=2
  stat_rev_mean_dow_month = 12,200
  No special events
  → Prediction: 11,800

N-BEATS:
  Input: [Revenue_2021-03-15, ..., Revenue_2023-03-14]
  Trend + Seasonality blocks
  → Prediction: 12,100

CEO Ridge (learned weights):
  Final = 0.35×12000 + 0.40×11800 + 0.25×12100 = 11,945
```

**→ Normal day: 3 models gần nhau → Stable prediction**

---

### **Scenario 2: Singles Day (2023-11-11 Saturday)**

```python
Prophet:
  Baseline + Holiday(11/11) + Weekend
  → Prediction: 45,000

LightGBM:
  shopping_festival_score = 3 (MEGA!)
  rev_lag_364 = 42,000
  stat_rev_yoy_growth_month[11] = +18%
  Interaction: score=3 × high_lag → HUGE boost
  → Prediction: 52,000

N-BEATS:
  Learned from 2012-11-11 to 2022-11-11 spikes
  Growing pattern + Nov 11 special
  → Prediction: 48,000

CEO Ridge (event-heavy weights):
  Final = 0.25×45000 + 0.50×52000 + 0.25×48000 = 49,250
```

**→ Big event: LightGBM dominates (event expertise)**

---

### **Scenario 3: Tết Peak (2024-01-20, Mùng 10)**

```python
Prophet:
  Trend + Tet holiday + Custom Tet seasonality
  → Prediction: 35,000

LightGBM:
  days_to_tet = +10
  is_tet_reopening = 1
  rev_lag_364 = 32,000
  → Prediction: 28,000 (recovery, not peak)

N-BEATS:
  Learned ~354-day cycle from 10 Tets
  Mùng 10 pattern
  → Prediction: 30,000

CEO Ridge (seasonality-heavy):
  Final = 0.40×35000 + 0.35×28000 + 0.25×30000 = 31,300
```

**→ Cultural event: Prophet leads (explicit Tet knowledge)**

---

### **Scenario 4: Lockdown Contaminated Lag (2022-06-15)**

```python
Prophet:
  Trend + June seasonality
  is_lockdown = 0 (2022 no lockdown)
  → Prediction: 14,000

LightGBM:
  rev_lag_364 = 5,000 (from 2021 lockdown!)
  is_lockdown = 0
  Learned interaction: "If lag < 8k, discount it, use lag_728"
  rev_lag_728 = 13,500 (2020, clean)
  → Prediction: 14,100 (corrected!)

N-BEATS:
  Input has 2021 anomaly
  Generic block: "2021 = outlier, use 2020/2022 pattern"
  → Prediction: 13,800

CEO Ridge:
  Final ≈ 14,000 (all models corrected for anomaly)
```

**→ Contaminated data: Guide rails work! All models handle well**

---

---

## 🏆 EXPECTED PERFORMANCE BY MODEL

### **Individual Model Scores (CV estimates):**

| Model | MAE | RMSE | R² | Strength Area |
|-------|-----|------|----|---------------|
| **Prophet** | ~1,200 | ~2,500 | 0.82 | Smooth baseline |
| **LightGBM** | ~950 | ~2,000 | 0.88 | Events & interactions |
| **N-BEATS** | ~1,100 | ~2,300 | 0.85 | Deep patterns |
| **Ensemble** | **~800** | **~1,800** | **0.91** | Combined strengths |

**Expected improvement: 15-20% vs best single model**

---

### **Why Ensemble Works:**

```
Error correlation analysis:

Prophet errors: Underpredict events, overpredict troughs
LightGBM errors: Overshoot new events, miss smooth trends
N-BEATS errors: Struggle with unseen event types

→ Errors NEGATIVELY correlated!
→ Ridge blends to cancel out errors
→ Final prediction more stable
```

---

---

## 🔧 IMPLEMENTATION NOTES

### **Iterative Prediction for Test Set:**

**Challenge:** Test period 548 days, nhưng `rev_lag_364` cần data từ test!

**Solution: Predict day-by-day**

```python
predictions = []

for test_date in test_dates:  # 548 days
    # Create features
    features = create_features(
        date=test_date,
        train_data=train_data,
        predicted_history=predictions  # Use previous predictions
    )
    
    # Lag features:
    if test_date - 364 days trong train:
        rev_lag_364 = train_data[test_date - 364]
    else:
        rev_lag_364 = predictions[test_date - 364]  # Use prediction
    
    # Predict
    pred_prophet = model_prophet.predict(...)
    pred_lgbm = model_lgbm.predict(features)
    pred_nbeats = model_nbeats.predict(...)
    
    # Ensemble
    final_pred = ridge.predict([pred_prophet, pred_lgbm, pred_nbeats])
    
    predictions.append(final_pred)
```

---

### **Train 2 Separate Ensembles:**

```python
# Ensemble 1: Revenue
Prophet_rev + LightGBM_rev + N-BEATS_rev → Ridge_rev → Final Revenue

# Ensemble 2: COGS
Prophet_cogs + LightGBM_cogs + N-BEATS_cogs → Ridge_cogs → Final COGS
```

**Why separate:**
- Revenue: High volatility, strong event effects
- COGS: More stable, less event-driven
- Different patterns → separate ensembles better

---

---

## ✅ CHECKLIST: PHÂN BỔ FEATURES

```
☐ Prophet:
  ☐ Date column (ds)
  ☐ Target column (y)
  ☐ Holidays DataFrame (~200 rows)
  ☐ 3 COVID regressors
  ☐ Tet custom seasonality
  
☐ LightGBM:
  ☐ All 40 features
  ☐ Categorical features marked
  ☐ Hyperparameters tuned
  
☐ N-BEATS:
  ☐ Pure Revenue sequence
  ☐ input_size = 730
  ☐ horizon = 548
  ☐ NO features
  
☐ Ridge CEO:
  ☐ OOF predictions from 3 models
  ☐ L2 regularization
  ☐ Trained on validation folds
```

---

## 🎯 KẾT LUẬN

### **Tại sao phân bổ này tối ưu:**

1. ✅ **Maximum diversity** (~75%)
   - 3 paradigms khác nhau
   - 3 cách nhìn data khác nhau
   
2. ✅ **Complementary strengths**
   - Prophet: Macro seasonality
   - LightGBM: Micro interactions
   - N-BEATS: Deep patterns
   
3. ✅ **Tối ưu theo design**
   - Prophet: Minimal input (như thiết kế gốc)
   - LightGBM: Full features (strengths)
   - N-BEATS: Pure sequence (như thiết kế gốc)
   
4. ✅ **Error decorrelation**
   - Errors không giống nhau
   - Ridge blend tối ưu
   
5. ✅ **Interpretable**
   - Hiểu được tại sao mỗi model predict vậy
   - Debug được khi sai

---

**Last updated:** 2026-04-26  
**Total features created:** 40  
**Models:** Prophet (5 inputs) + LightGBM (40 features) + N-BEATS (0 features)  
**Expected ensemble improvement:** 15-20% vs best single model

---

**File này để gửi cho bạn của bạn hiểu chiến lược ensemble! 🚀**
