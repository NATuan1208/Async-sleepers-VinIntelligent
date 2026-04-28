# 🎯 DATATHON 2026 — MODELING STRATEGY (Phần 3)
## Sales Forecasting cho Fashion E-commerce Việt Nam

> **Mục tiêu:** Top 3 leaderboard Kaggle + Báo cáo kỹ thuật 7-8/8 điểm
> **Tổng điểm Phần 3:** 20đ (12đ hiệu suất + 8đ báo cáo)
> **Horizon:** 548 ngày (01/01/2023 → 01/07/2024)
> **Train data:** 04/07/2012 → 31/12/2022 (~3,833 ngày)

---

## 💻 Hardware Profile — Google Colab Free T4

> **Môi trường thực thi:** Google Colab Free, GPU NVIDIA Tesla T4

### Thông số đã verify

| Thành phần | Thông số | Ghi chú |
|---|---|---|
| GPU | NVIDIA Tesla T4 | Turing architecture, không phải Ampere |
| VRAM | **15GB usable** (16GB marketed − 1GB ECC) | ECC dùng cho error correction |
| CUDA Cores | 2,560 | Tensor Cores có, hỗ trợ FP16 mixed precision |
| CUDA Version | 12.x (tuỳ runtime) | Cần check với `!nvidia-smi` |
| CPU RAM | ~12-13GB | Tuỳ session, có thể thay đổi |
| GPU Availability | **KHÔNG được đảm bảo** | Đôi khi bị assign K80 (12GB, chậm hơn) |
| Session timeout | ~12h liên tục, ~1h idle disconnect | Cần save checkpoint định kỳ |

### Allocation quyết định: model nào chạy ở đâu

Đây là insight quan trọng nhất về hardware:

| Model | Hardware | Lý do |
|---|---|---|
| LightGBM (3 variants) | **CPU** | Dataset chỉ 3,833 rows ≈ 1.5MB → fit vào L2 cache. GPU overhead > speed-up. Train xong < 5 phút/variant trên CPU. |
| Prophet | **CPU** | Stan MCMC backend, không dùng CUDA. GPU = wasted. |
| N-BEATS | **GPU T4** | Neural network, PyTorch, mới cần CUDA. ~500 steps × batch=32 → ~10-15 phút trên T4. |

**Kết luận thực tế:** 80% pipeline chạy CPU, chỉ N-BEATS mới cần GPU. Colab T4 là đủ.

### Workflow do không có GPU local

```
Local machine (Claude Code):
├── Stage 0: Patch FE code
├── Stage 1: Build validation framework
├── Stage 2: Viết model code (không train)
├── Stage 3-5: Viết ensemble + SHAP + submission code
└── Output: colab_pipeline.ipynb (notebook hoàn chỉnh)

Google Colab T4 (chạy manually):
├── Upload: colab_pipeline.ipynb + data/ folder
├── Run Stage 2: LightGBM → CPU runtime (hoặc GPU đều được)
├── Run Stage 2: Prophet → CPU runtime
├── Run Stage 2: N-BEATS → GPU T4 runtime (BẮT BUỘC enable GPU)
├── Run Stage 3-5: Ensemble + SHAP + Submit → CPU
└── Download: submission.csv + shap_*.png + models/
```

### Memory management cho T4 (15GB VRAM)

N-BEATS với config hiện tại (`mlp_units=[[512,512],[512,512]]`, `input_size=730`, `batch_size=32`):
- Estimated VRAM usage: ~2-3GB → **an toàn, không OOM**
- Nếu OOM: reduce `batch_size=16`, `mlp_units=[[256,256],[256,256]]`

```python
# Đầu mỗi Colab cell, kiểm tra GPU được assign:
import subprocess
result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
                         "--format=csv,noheader"], capture_output=True, text=True)
print(result.stdout)
# Expected: Tesla T4, 15109 MiB total
# Nếu ra K80 → restart runtime để reroll GPU assignment
```

### Session management để tránh mất work

```python
# Save model sau mỗi stage training:
import pickle, os

os.makedirs("checkpoints", exist_ok=True)
with open("checkpoints/lgb_huber.pkl", "wb") as f:
    pickle.dump(lgb_huber_model, f)

# Save predictions array:
np.save("checkpoints/lgb_huber_oof.npy", oof_lgb_huber)
np.save("checkpoints/lgb_huber_test.npy", test_lgb_huber)

# → Download checkpoints/ về local sau khi train xong mỗi model
#   để không mất nếu session crash
```

---

## 📐 Triết lý thiết kế

Plan này **KHÔNG** phải plan đầy tham vọng nhất — nó là plan **có xác suất cao nhất đạt top 3** với team 2-3 người, > 5 ngày bandwidth, PyTorch beginner.

**Bốn nguyên tắc bất biến:**

1. **Recursive forecasting với lag_364 là chiến lược chủ đạo** — không bỏ chỉ vì sợ "leakage". M5 Walmart winner cũng dùng cách này.
2. **Diversity > Complexity** — 5 model đơn giản blend tốt hơn 1 model phức tạp.
3. **Mọi quyết định phải có anti-leakage assertion** — bài thi loại nếu vi phạm.
4. **SHAP + business translation là bắt buộc** — đó là 8đ báo cáo trong tầm tay.

---

## 🏗️ Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 0: Data Audit & Feature Prep (đã có 80% code)        │
│  → Output: X_train, y_train, X_test (templates)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: Validation Framework (BẮT BUỘC trước modeling)    │
│  • TimeSeriesSplit với gap & test_size phù hợp horizon      │
│  • Adversarial validation (train vs test distribution)      │
│  • Hard assertions cho leakage detection                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: Base Models (5 models, recursive forecast)        │
│  ├── LightGBM Huber (log1p + Jensen correction)             │
│  ├── LightGBM L1/MAE                                        │
│  ├── LightGBM Tweedie                                       │
│  ├── Prophet (multiplicative + VN holidays)                 │
│  └── N-BEATS (univariate, fallback)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: Ensemble Blending                                 │
│  • SLSQP non-negative weights (KHÔNG dùng Ridge)            │
│  • Fallback: equal weights nếu val < 60 ngày                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 4: COGS Prediction                                   │
│  • Rolling 90-day margin ratio (default)                    │
│  • Hoặc separate model nếu CV(margin) > 0.20                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 5: SHAP Analysis & Submission                        │
│  • TreeSHAP cho LightGBM best variant                       │
│  • Business translation table (SHAP → VND insights)         │
│  • Validate submission format vs sample_submission.csv      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 Anti-Leakage Rules — KHÔNG ĐƯỢC VI PHẠM

Theo đề bài Phần 3.6, có **3 điều kiện loại bài tuyệt đối**:

> 1. Sử dụng Revenue/COGS từ tập test làm đặc trưng
> 2. Sử dụng dữ liệu ngoài bộ dữ liệu được cung cấp
> 3. Không đính kèm mã nguồn hoặc kết quả không thể tái lập

### Rules cụ thể

| Rule | Implementation | Khi nào check |
|------|---------------|---------------|
| Train end < Val start | `assert X_tr.index.max() < X_val.index.min()` | Mỗi CV fold |
| Statistics tính chỉ từ train | `_compute_statistics(train_only)` | Mỗi fold + final fit |
| Lag features dùng historical revenue | Recursive: predicted Revenue làm proxy cho test | Build test features |
| Random seed = 42 mọi nơi | `random_state=42` trong tất cả model | Mọi stochastic op |
| Submission row count match | `assert len(sub) == len(sample_submission)` | Trước save CSV |
| Submission date order match | `assert (sub.Date == sample_sub.Date).all()` | Trước save CSV |
| No NaN trong submission | `assert sub.notna().all().all()` | Trước save CSV |
| Revenue/COGS ≥ 0 | `np.clip(pred, 0, None)` | Sau predict |

### Pattern code anti-leakage

```python
def assert_no_leakage(X_train, X_val, y_train, y_val, fold_idx):
    """Run BEFORE every fit() call."""
    assert X_train.index.max() < X_val.index.min(), (
        f"FOLD {fold_idx} LEAKAGE: train_max={X_train.index.max()} "
        f">= val_min={X_val.index.min()}"
    )
    assert len(X_train) == len(y_train), "X/y length mismatch in train"
    assert len(X_val) == len(y_val), "X/y length mismatch in val"
    assert not y_train.isna().any(), "NaN in y_train"
    assert not y_val.isna().any(), "NaN in y_val"
    print(f"✅ Fold {fold_idx} anti-leakage assertions passed")
```

---

## 🔧 STAGE 0 — Feature Engineering Patches

Code `feature_preparation.py` hiện tại đã tốt 80%. Cần **4 patches nhỏ** trước khi train:

### Patch 1: Era-gate cho mega sales

11/11 chỉ bùng nổ ở VN từ 2017+, 12/12 từ 2014+. Không gate → model học sai pattern.

```python
# Trong _calc_shopping_festival_score, thêm year check:
def _calc_shopping_festival_score(date: pd.Timestamp) -> int:
    month_day = (date.month, date.day)
    year = date.year
    if month_day == (11, 11) and year >= 2017:
        return 3
    if month_day == (12, 12) and year >= 2014:
        return 3
    if month_day == (9, 9) and year >= 2016:
        return 2
    if month_day == (10, 10) and year >= 2016:
        return 2
    if date.month == date.day and 1 <= date.day <= 8:
        return 1
    return 0
```

### Patch 2: TikTok Shop era flag

TikTok Shop launch VN: 28/04/2022 → có structural change cuối train period.

```python
# Thêm vào LIGHTGBM_FEATURE_COLUMNS:
"is_tiktok_era",

# Trong prepare_lightgbm_features:
features["is_tiktok_era"] = (dates >= pd.Timestamp("2022-04-28")).astype(int)
```

### Patch 3: Year as numeric feature

LightGBM cần explicit trend signal. Hiện tại không có `year` → model phải học trend qua statistics → sub-optimal.

```python
# Thêm vào LIGHTGBM_FEATURE_COLUMNS:
"year",

# Trong prepare_lightgbm_features:
features["year"] = dates.dt.year
```

### Patch 4: Sales date completeness check

Verify không có ngày missing trước khi tạo lag features:

```python
def _validate_continuity(base: pd.DataFrame) -> None:
    expected = pd.date_range(base["Date"].min(), base["Date"].max(), freq="D")
    actual = pd.DatetimeIndex(base["Date"])
    missing = expected.difference(actual)
    if len(missing) > 0:
        raise ValueError(
            f"Sales has {len(missing)} missing dates. "
            f"First 5: {missing[:5].tolist()}. "
            f"Reindex + ffill before feature engineering."
        )
```

**Sau khi patch:** Tổng feature count = **42** (40 cũ + `is_tiktok_era` + `year`).

---

## 📊 STAGE 1 — Validation Framework

### CV strategy

```python
from sklearn.model_selection import TimeSeriesSplit

# Critical params:
# - n_splits=5: đủ folds để có CV signal mạnh
# - gap=30: 30 ngày buffer giữa train end và val start
#   (tránh rolling features từ train leak vào val)
# - test_size=180: mỗi val fold = 6 tháng
#   (1 năm như plan cũ quá rộng → CV không stable)

tscv = TimeSeriesSplit(
    n_splits=5,
    gap=30,
    test_size=180,
)
```

### Adversarial validation — bắt buộc

Train classifier phân biệt train vs test. AUC < 0.7 = OK; AUC > 0.85 = distribution shift nghiêm trọng.

```python
def adversarial_validation(X_train, X_test):
    """Returns AUC. Higher = more distribution shift."""
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score

    X_combined = pd.concat([X_train, X_test], axis=0).reset_index(drop=True)
    y_combined = np.concatenate([
        np.zeros(len(X_train)),
        np.ones(len(X_test)),
    ])

    clf = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        random_state=42,
        verbose=-1,
    )
    # Drop target & date columns trước khi fit
    feature_cols = [c for c in X_combined.columns if c not in ["Date", "target"]]
    clf.fit(X_combined[feature_cols], y_combined)

    auc = roc_auc_score(
        y_combined,
        clf.predict_proba(X_combined[feature_cols])[:, 1]
    )

    print(f"Adversarial AUC: {auc:.3f}")
    if auc > 0.85:
        print("⚠️ HIGH DISTRIBUTION SHIFT — review features")
    elif auc > 0.70:
        print("⚠️ Moderate shift — monitor important features")
    else:
        print("✅ Distributions similar — CV trustworthy")

    # Top features causing shift (debug aid)
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": clf.feature_importances_,
    }).sort_values("importance", ascending=False)
    print("Top 10 shift-causing features:")
    print(importance.head(10))

    return auc
```

---

## 🤖 STAGE 2 — Base Models

### Tại sao 5 models này, KHÔNG phải khác

| Model | Vai trò trong ensemble | Diversity source |
|-------|------------------------|------------------|
| LightGBM Huber + log1p | Best single performer, robust outliers | Loss function |
| LightGBM L1/MAE | MAE-consistent với metric chính | Loss function |
| LightGBM Tweedie | Heavy-tail (Tết spike, 11/11) | Loss distribution |
| Prophet | Holiday effects, multiplicative | Architecture (additive decomposition) |
| N-BEATS | End-to-end neural, no FE assumption | Architecture (deep learning) |

### Tại sao KHÔNG dùng N-HiTS / Chronos / TiDE

- **Bandwidth:** 5 ngày không đủ cho 3 neural models phức tạp với team beginner PyTorch
- **ROI thấp:** N-HiTS hơn N-BEATS ~3% MAE — không đủ để justify rủi ro debug
- **Chronos-Bolt:** Có lý nhưng cần AutoGluon + GPU consistent → để vào "stretch goal"

### LightGBM config (3 variants)

```python
# Common base params
LGB_BASE_PARAMS = {
    "verbose": -1,
    "n_jobs": -1,
    "random_state": 42,
    "n_estimators": 5000,  # FIX, không tune cùng learning_rate
    "early_stopping_rounds": 200,
    "learning_rate": 0.03,
    "num_leaves": 127,
    "max_depth": -1,
    "min_child_samples": 30,
    "feature_fraction": 0.7,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "reg_alpha": 0.05,
    "reg_lambda": 0.1,
}

# Variant 1: Huber loss + log1p target (best single performer)
LGB_HUBER_PARAMS = {
    **LGB_BASE_PARAMS,
    "objective": "huber",
    "alpha": 0.9,  # Huber threshold
    "metric": "mae",
    # Note: target được transform log1p TRƯỚC khi fit
    # Inverse với Jensen correction sau predict
}

# Variant 2: L1/MAE (consistent với metric)
LGB_L1_PARAMS = {
    **LGB_BASE_PARAMS,
    "objective": "regression_l1",
    "metric": "mae",
}

# Variant 3: Tweedie (handle heavy-tail)
LGB_TWEEDIE_PARAMS = {
    **LGB_BASE_PARAMS,
    "objective": "tweedie",
    "tweedie_variance_power": 1.5,  # Between Poisson (1) and Gamma (2)
    "metric": "mae",
}
```

### Jensen's Inequality bias correction (CRITICAL cho Huber variant)

Đây là silent bug 90% team mắc. KHÔNG được skip.

```python
def fit_predict_lgb_with_log_target(X_train, y_train, X_val, y_val, X_test, params):
    """
    Train LightGBM trên log1p(y) và predict với Jensen correction.

    Lý do Jensen correction:
        E[exp(X)] ≠ exp(E[X])
        → expm1(model.predict(X)) cho ra MEDIAN, không phải MEAN
        → underestimate hệ thống 5-15% khi metric là MAE/RMSE
    """
    y_train_log = np.log1p(y_train)
    y_val_log = np.log1p(y_val)

    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train_log,
        eval_set=[(X_val, y_val_log)],
        callbacks=[lgb.early_stopping(200), lgb.log_evaluation(0)],
    )

    # Compute residual variance for Jensen correction
    train_pred_log = model.predict(X_train)
    residuals = y_train_log.values - train_pred_log
    sigma2 = np.var(residuals)

    # Predict val & test with bias correction
    val_pred_log = model.predict(X_val)
    test_pred_log = model.predict(X_test)

    val_pred = np.expm1(val_pred_log + sigma2 / 2)
    test_pred = np.expm1(test_pred_log + sigma2 / 2)

    # Clip non-negative
    val_pred = np.clip(val_pred, 0, None)
    test_pred = np.clip(test_pred, 0, None)

    return model, val_pred, test_pred, sigma2
```

### Recursive forecast cho test set 548 ngày

**Đây là phần phức tạp nhất.** Code phải build test features từng ngày một, dùng prediction của LightGBM để fill `rev_lag_364` cho các ngày test sau.

```python
def recursive_forecast(model, sales_history, test_dates, feature_builder, statistics):
    """
    Predict test set với recursive strategy.

    Args:
        model: trained LightGBM
        sales_history: train + already-predicted test dates
                       (DataFrame với cột Date, Revenue, COGS)
        test_dates: DatetimeIndex của ngày cần predict
        feature_builder: function(history_df) → X
        statistics: pre-computed dict từ TRAIN ONLY
    """
    history = sales_history.copy().sort_values("Date").reset_index(drop=True)
    predictions = []

    for test_date in test_dates:
        # Build features cho ngày này (lag_364 lấy từ history đã có)
        single_row_df = pd.DataFrame({
            "Date": [test_date],
            "Revenue": [np.nan],  # placeholder
            "COGS": [np.nan],
        })
        # Append vào history để feature_builder có thể compute lag
        extended = pd.concat([history, single_row_df], ignore_index=True)
        features_full = feature_builder(extended, statistics=statistics)

        # Lấy row cuối (chính là test_date)
        X_today = features_full.iloc[-1:][LIGHTGBM_FEATURE_COLUMNS]

        # Predict
        pred = float(model.predict(X_today)[0])
        pred = max(0.0, pred)  # clip non-negative

        # Append prediction vào history (để ngày sau dùng làm lag)
        history = pd.concat([
            history,
            pd.DataFrame({
                "Date": [test_date],
                "Revenue": [pred],
                "COGS": [np.nan],  # COGS predict riêng
            }),
        ], ignore_index=True)

        predictions.append(pred)

    return np.array(predictions)
```

### Prophet config

```python
def train_prophet(train_df, holidays_df, regressors_df=None):
    """
    train_df: DataFrame với cột [ds, y]
    holidays_df: từ prepare_prophet_features
    regressors_df: COVID regressors (optional)
    """
    from prophet import Prophet

    m = Prophet(
        yearly_seasonality=10,  # Higher fourier order cho fashion
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",  # Fashion → spike-heavy
        changepoint_prior_scale=0.05,  # Conservative vs COVID structural break
        seasonality_prior_scale=15.0,
        holidays_prior_scale=20.0,
        holidays=holidays_df,
        interval_width=0.95,
    )

    if regressors_df is not None:
        for col in regressors_df.columns:
            m.add_regressor(col)
        train_full = train_df.merge(regressors_df, on="ds")
    else:
        train_full = train_df

    m.fit(train_full)
    return m
```

### N-BEATS config — Optimized cho T4 15GB VRAM

> **Chạy trên Colab T4 GPU.** CPU runtime sẽ chậm hơn ~10x, không khuyến nghị.

```python
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS
from neuralforecast.losses.pytorch import MAE
import torch

def train_nbeats(y_series, dates, horizon=548):
    # Verify GPU available trước khi train
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("⚠️ WARNING: No GPU detected. N-BEATS on CPU will be slow (~2-3h).")
        print("   → Enable GPU: Runtime > Change runtime type > T4 GPU")
        print("   → Nếu buộc phải dùng CPU: reduce max_steps=150, batch_size=64")

    # Estimated VRAM: ~2-3GB với config này → an toàn trên T4 (15GB usable)
    train_df = pd.DataFrame({
        "ds": dates,
        "y": y_series,
        "unique_id": "total_revenue",
    })

    model = NeuralForecast(
        models=[
            NBEATS(
                h=horizon,
                input_size=2 * 365,       # 730 days lookback, ~1.5MB data → OK
                stack_types=["trend", "seasonality"],
                n_blocks=[3, 3],
                mlp_units=[[512, 512], [512, 512]],  # ~2GB VRAM, safe on T4
                n_harmonics=2,
                n_polynomials=2,
                dropout_prob_theta=0.1,
                learning_rate=1e-3,
                max_steps=500,            # ~10-15 min trên T4
                batch_size=32,
                random_seed=42,
                loss=MAE(),
                # accelerator tự động detect GPU nếu torch.cuda.is_available()
            ),
        ],
        freq="D",
    )

    print(f"Training N-BEATS on {device.upper()}...")
    model.fit(train_df)
    return model


# Fallback config nếu OOM hoặc K80 được assign (12GB VRAM):
NBEATS_FALLBACK_CONFIG = {
    "mlp_units": [[256, 256], [256, 256]],  # Giảm ~50% VRAM
    "batch_size": 16,
    "max_steps": 300,
}
```

---

## 🎭 STAGE 3 — Ensemble Blending

### Tại sao SLSQP, KHÔNG phải Ridge

M5 Walmart Competition (50,000+ teams) winner dùng **equal-weighted average**. Top-3 dùng arithmetic mean. Chỉ teams ngoài top-25 mới dùng Ridge/learned weights.

**Lý do thống kê:**
- Validation data ngắn (~180 ngày) → sai số ước lượng weights LỚN HƠN lợi ích optimization
- Ridge có thể cho weight ÂM → "trừ đi" prediction của model đó → vô nghĩa
- SLSQP với constraint `w ≥ 0, sum = 1` → an toàn về mặt thống kê

### Implementation

```python
from scipy.optimize import minimize

def fit_ensemble_weights(oof_predictions: np.ndarray, y_val: np.ndarray) -> np.ndarray:
    """
    Fit non-negative weights via SLSQP minimizing MAE.

    Args:
        oof_predictions: shape (n_samples, n_models)
        y_val: shape (n_samples,)

    Returns:
        weights: shape (n_models,), non-negative, sum to 1
    """
    n_models = oof_predictions.shape[1]

    # Fallback: nếu val ngắn → equal weights
    if len(y_val) < 60:
        print("⚠️ Val < 60 days → using equal weights")
        return np.ones(n_models) / n_models

    def objective(w):
        y_pred = oof_predictions @ w
        return np.mean(np.abs(y_pred - y_val))

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bounds = [(0.0, 1.0)] * n_models
    w0 = np.ones(n_models) / n_models  # init từ equal weights

    result = minimize(
        objective, w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if not result.success:
        print(f"⚠️ SLSQP failed: {result.message}. Using equal weights.")
        return np.ones(n_models) / n_models

    weights = result.x
    print(f"Ensemble weights: {dict(zip([f'model_{i}' for i in range(n_models)], weights.round(3)))}")
    return weights
```

### Snapshot ensembling cho LightGBM (free improvement)

Train 3 seeds (42, 123, 7) cho mỗi LGB variant → average predictions. Cost: 3x train time. Gain: ~2-5% MAE.

```python
def train_lgb_with_seed_bagging(X_train, y_train, X_val, y_val, X_test, params, seeds=(42, 123, 7)):
    val_preds = []
    test_preds = []
    for seed in seeds:
        params_seeded = {**params, "random_state": seed}
        model = lgb.LGBMRegressor(**params_seeded)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                  callbacks=[lgb.early_stopping(200), lgb.log_evaluation(0)])
        val_preds.append(model.predict(X_val))
        test_preds.append(model.predict(X_test))
    return np.mean(val_preds, axis=0), np.mean(test_preds, axis=0)
```

---

## 💰 STAGE 4 — COGS Prediction

### Strategy decision tree

```
Compute CV(margin) trong 90 ngày cuối train:
    margin = COGS / Revenue
    cv = margin.rolling(90).std().iloc[-1] / margin.rolling(90).mean().iloc[-1]

if cv < 0.08:
    # Margin ổn định → ratio approach
    ratio = margin.rolling(90).mean().iloc[-1]
    cogs_pred = revenue_pred * ratio

elif cv < 0.20:
    # Margin biến động vừa → train COGS model riêng
    # Dùng cùng feature set + cùng pipeline
    cogs_pred = lgb_cogs.predict(X_test)

else:
    # Margin biến động mạnh → blend 50/50
    cogs_pred_ratio = revenue_pred * margin.rolling(90).mean().iloc[-1]
    cogs_pred_model = lgb_cogs.predict(X_test)
    cogs_pred = 0.5 * cogs_pred_ratio + 0.5 * cogs_pred_model
```

**Theo data_profile.json:** Avg gross margin = 12.54% → margin = 87.46%. CV cần check nhưng có vẻ stable → likely dùng **ratio approach**.

---

## 🔍 STAGE 5 — SHAP Analysis & Submission

### SHAP cho 8đ báo cáo

```python
import shap

def generate_shap_analysis(model, X_train, X_sample_size=2000):
    """Generate SHAP plots + business translation table."""
    # Sample để tránh OOM
    sample_idx = np.random.RandomState(42).choice(
        len(X_train), size=min(X_sample_size, len(X_train)), replace=False
    )
    X_sample = X_train.iloc[sample_idx]

    explainer = shap.TreeExplainer(
        model,
        feature_perturbation="interventional",
        data=X_train.sample(200, random_state=42),
    )
    shap_values = explainer.shap_values(X_sample)

    # Save artifacts
    np.save("shap_values.npy", shap_values)

    # Plot 1: Beeswarm
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_sample, max_display=20, show=False)
    plt.title("SHAP Feature Importance — Revenue Forecasting")
    plt.tight_layout()
    plt.savefig("shap_beeswarm.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 2: Bar (mean absolute)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, plot_type="bar", max_display=20, show=False)
    plt.tight_layout()
    plt.savefig("shap_bar.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 3: Waterfall cho ngày Tết-eve điển hình
    tet_eve_2022 = pd.Timestamp("2022-01-31")
    if tet_eve_2022 in X_train.index:
        idx = X_train.index.get_loc(tet_eve_2022)
        shap.waterfall_plot(
            shap.Explanation(
                values=shap_values[idx],
                base_values=explainer.expected_value,
                data=X_train.iloc[idx].values,
                feature_names=X_train.columns.tolist(),
            ),
            show=False,
        )
        plt.savefig("shap_waterfall_tet_eve.png", dpi=150, bbox_inches="tight")
        plt.close()

    # Importance dataframe
    importance_df = pd.DataFrame({
        "feature": X_train.columns,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)
    importance_df.to_csv("shap_importance.csv", index=False)

    return shap_values, importance_df
```

### Business translation template

| SHAP Feature | Business Translation cho báo cáo |
|---|---|
| `rev_lag_364` rank #1 | *"Doanh thu cùng thứ năm ngoái giải thích nhiều variance nhất → annual seasonality cực ổn định, brand có predictability cao."* |
| `stat_rev_mean_dow_month` top 3 | *"Pattern lookup từ 10 năm wisdom → general rules đáng tin hơn lag features bị COVID contaminate."* |
| `days_to_tet` SHAP +120M VND | *"Window 7-14 ngày trước Tết tạo spike +120M VND trung bình → tăng inventory 3 tuần trước Tết."* |
| `is_lockdown` SHAP -450M VND | *"COVID lockdown làm giảm 450M VND/ngày → cần buffer plan cho rủi ro gián đoạn tương lai."* |
| `is_payday_window` SHAP +60M | *"Spike cuối tháng (lương về) +60M VND → tập trung campaign 25-31 hàng tháng."* |
| `shopping_festival_score` rank 4 | *"Hierarchy 11/11 (3) > 9/9 (2) > 1/1 (1) phản ánh đúng thực tế thị trường VN."* |

### Submission validation (BẮT BUỘC)

```python
def validate_submission(submission_df, sample_submission_df):
    """Hard checks trước khi save submission.csv."""
    # Check 1: Row count
    assert len(submission_df) == len(sample_submission_df), (
        f"Row mismatch: {len(submission_df)} vs {len(sample_submission_df)}"
    )

    # Check 2: Column order
    assert list(submission_df.columns) == ["Date", "Revenue", "COGS"], (
        f"Wrong columns: {submission_df.columns.tolist()}"
    )

    # Check 3: Date order match
    sub_dates = pd.to_datetime(submission_df["Date"]).values
    sample_dates = pd.to_datetime(sample_submission_df["Date"]).values
    assert (sub_dates == sample_dates).all(), "Date order mismatch with sample"

    # Check 4: No NaN
    assert not submission_df.isna().any().any(), "NaN in submission"

    # Check 5: Non-negative
    assert (submission_df["Revenue"] >= 0).all(), "Negative Revenue"
    assert (submission_df["COGS"] >= 0).all(), "Negative COGS"

    # Check 6: COGS < Revenue (business rule)
    assert (submission_df["COGS"] <= submission_df["Revenue"]).all(), "COGS > Revenue"

    # Check 7: Reasonable magnitude (avg daily revenue 2012-2022 = 4.28M)
    rev_mean = submission_df["Revenue"].mean()
    assert 500_000 < rev_mean < 50_000_000, (
        f"Revenue mean suspicious: {rev_mean:,.0f}"
    )

    print("✅ All submission checks passed")
    print(f"  Rows: {len(submission_df)}")
    print(f"  Date range: {submission_df['Date'].min()} → {submission_df['Date'].max()}")
    print(f"  Revenue: mean={submission_df['Revenue'].mean():,.0f}, "
          f"min={submission_df['Revenue'].min():,.0f}, "
          f"max={submission_df['Revenue'].max():,.0f}")
```

---

## 📁 Cấu trúc file output mong đợi

```
/project_root/                        ← Local machine (Claude Code viết code)
├── data/                             # Read-only
│   ├── sales.csv
│   ├── sample_submission.csv
│   └── ... (các CSV khác)
├── src/
│   ├── feature_preparation.py        # Đã có, áp dụng 4 patches
│   ├── validation.py                 # CV + adversarial + assertions
│   ├── models.py                     # LightGBM variants + Prophet + N-BEATS
│   ├── ensemble.py                   # SLSQP blender
│   ├── shap_analysis.py              # SHAP plots + business translation
│   └── recursive_forecast.py         # Recursive predict logic
├── colab_pipeline.ipynb              # ← NOTEBOOK CHÍNH upload lên Colab
├── outputs/
│   ├── submission.csv                # Download từ Colab sau khi run xong
│   ├── shap_beeswarm.png             # Download từ Colab
│   ├── shap_bar.png
│   ├── shap_waterfall_tet_eve.png
│   ├── shap_importance.csv
│   └── cv_results.csv
└── checkpoints/                      # Download từ Colab định kỳ
    ├── lgb_huber.pkl                 # Trained models
    ├── lgb_l1.pkl
    ├── lgb_tweedie.pkl
    ├── lgb_huber_oof.npy             # OOF predictions
    ├── lgb_huber_test.npy            # Test predictions per model
    └── nbeats_oof.npy

Google Colab T4 runtime:              ← Train ở đây, download về local
├── Cần upload: colab_pipeline.ipynb + data/ folder
├── CPU tasks: LightGBM × 3, Prophet (không cần enable GPU)
├── GPU tasks: N-BEATS only (Runtime > Change runtime type > T4 GPU)
└── Download sau khi xong: checkpoints/ + outputs/
```

---

## ⏱️ Timeline thực thi (5-7 ngày)

| Day | Task | Chạy ở đâu | Hours | Output |
|-----|------|------------|-------|--------|
| 1 | Apply 4 FE patches + build validation framework | Local | 3h | `feature_preparation.py` v2 + `validation.py` |
| 1 | Viết model code (LightGBM variants + Prophet) | Local | 3h | `models.py` (code only, chưa train) |
| 2 | Viết recursive_forecast, ensemble, SHAP, submission code | Local | 4h | Tất cả `src/` files hoàn chỉnh |
| 2 | Tạo `colab_pipeline.ipynb` hoàn chỉnh | Local | 2h | Notebook sẵn sàng upload |
| 3 | **Upload lên Colab, train LightGBM × 3** | **Colab CPU** | 3h | OOF + test predictions, checkpoint files |
| 3 | **Train Prophet** | **Colab CPU** | 1h | OOF + test predictions |
| 3 | **Train N-BEATS** (enable GPU T4 trước!) | **Colab GPU T4** | 1h | OOF + test predictions |
| 3 | **SLSQP blend + COGS + SHAP + First submission** | **Colab CPU** | 2h | `submission.csv` trên Kaggle |
| 4 | Iterate: tune hyperparams nếu LB < top 5 | Colab | 4h | Better submission |
| 5-6 | Report writing (NeurIPS template, ≤ 4 trang) | Local | 6h | PDF report |
| 6-7 | Buffer: iterate + report finalize | Both | 4h | Final submission |

### ⚠️ Colab session tips

1. **Trước khi train N-BEATS:** `Runtime > Change runtime type > T4 GPU` → `Connect`
2. **Verify GPU:** `!nvidia-smi` → phải thấy `Tesla T4` và `15109 MiB` free
3. **Nếu ra K80:** Disconnect → `Runtime > Disconnect and delete runtime` → reconnect (reroll)
4. **Định kỳ download checkpoints** sau mỗi model train xong — session có thể crash
5. **Notebook phải tự-contained:** Cell đầu tiên install tất cả packages, cell thứ 2 upload data

---

## 🎯 Acceptance Criteria

### Code (bắt buộc trước khi commit)

- [ ] All 5 base models train without error
- [ ] CV MAE < 1.5M VND (rough sanity check, có thể tighter sau khi run)
- [ ] Anti-leakage assertions pass mọi fold
- [ ] Adversarial AUC < 0.85
- [ ] Submission validation passes all 7 checks
- [ ] `random_state=42` set ở mọi stochastic operation
- [ ] Code chạy end-to-end từ raw data → submission.csv trong 1 command

### Báo cáo (cho 8đ technical report)

- [ ] CV protocol diagram (TimeSeriesSplit visualization)
- [ ] Anti-leakage measures section (explicit list các assertions)
- [ ] CV performance table per fold
- [ ] SHAP beeswarm + bar plots
- [ ] Top 10 features với business interpretation
- [ ] Reproducibility statement + GitHub link

### Submission (cho 12đ performance)

- [ ] Format match `sample_submission.csv` 100%
- [ ] Submitted trên Kaggle trước deadline
- [ ] At least 2 Kaggle submissions để compare LB scores

---

## 🚧 Risk Register

| Rủi ro | Khả năng | Impact | Mitigation |
|--------|----------|--------|-----------|
| `lag_364` leakage trong test set | Cao | Loại bài | Recursive forecast: dùng prediction làm proxy cho `lag_364` test rows |
| Jensen bias bị skip | Cao | -10% MAE | Code review checklist trước commit |
| Adversarial AUC > 0.9 | Trung bình | CV không đáng tin | Drop high-shift features, dùng holdout 6 tháng cuối |
| N-BEATS training timeout | Trung bình | Mất 1 model | Reduce `max_steps`, fallback drop khỏi ensemble |
| Recursive forecast bug | Cao | -20% accuracy | Unit test trên 30-day rolling validation |
| COGS predictions ≥ Revenue | Trung bình | Business rule violation | Hard clip: `cogs = min(cogs_pred, 0.95 * revenue_pred)` |
| Submission row order sai | Thấp | 0đ Phần 3 | `validate_submission()` BẮT BUỘC trước save |
| Kaggle public LB ≠ private LB | Trung bình | Mất top 3 | Submit 2 strategies (best CV + ensemble), pick safer |

---

## 📖 References for code generation

Code sẽ generate phải reference các best practices từ:

1. **M5 Walmart Forecasting (Kaggle)**: Recursive với LightGBM + lag_28/365, equal-weighted ensemble
2. **`feature_preparation.py` hiện có**: 80% logic đã đúng, chỉ patch 4 chỗ
3. **Strategy v2 (DATATHON2026_Strategy_Prompt_v2.md)**: Cấu trúc tổng thể giữ nguyên
4. **Anti-leakage rules**: Đề bài Phần 3.6 conditions

---

## ❌ ANTI-PATTERNS — KHÔNG ĐƯỢC LÀM

1. ❌ **Bỏ `lag_364`** vì sợ leakage → đây là feature mạnh nhất, recursive forecast giải quyết được
2. ❌ **Polynomial detrending bậc 2** → COVID làm trend non-monotonic → sẽ extrapolate sai
3. ❌ **Random KFold cross-validation** → leakage bự, CV score vô nghĩa
4. ❌ **Ridge meta-learner** → có thể cho weight âm, dùng SLSQP
5. ❌ **Skip Jensen correction** khi dùng log1p target → underestimate hệ thống
6. ❌ **Train N-HiTS + TiDE + Chronos** với team beginner PyTorch → over-engineering
7. ❌ **Tune `n_estimators`** trong Optuna → fix 5000 + early_stopping
8. ❌ **Dùng `revenue_pred` của ngày test trong feature** → leakage ngầm, recursive xử lý đúng
9. ❌ **Skip adversarial validation** → không biết CV có đáng tin không
10. ❌ **Submit không validate format** → có thể bị Kaggle reject

---

## ✅ SUCCESS METRICS

- **Mục tiêu MAE:** < 800,000 VND (so với mean daily revenue 4.28M)
- **Mục tiêu R²:** > 0.85
- **Mục tiêu Kaggle rank:** Top 5 public LB → top 3 private LB
- **Báo cáo:** 7-8/8 điểm với pipeline rõ ràng + SHAP business translation

---

*Strategy version 1.0 — Calibrated for: Team 2-3 người, > 5 ngày, PyTorch beginner, có experience ensemble*
*DATATHON 2026 — The Gridbreaker, VinTelligence / VinUniversity*
