# 🚀 IMPLEMENTATION GUIDE: 3 FEATURE PREPARATION FUNCTIONS

**Target:** Claude Code (Terminal AI Assistant)  
**Task:** Implement 3 functions để chuẩn bị features cho Prophet, LightGBM, N-BEATS  
**Test:** Verify với 5 dòng đầu của `sales.csv`

---

## 📚 BỐI CẢNH - ĐỌC TRƯỚC KHI CODE

### **Step 0: Đọc 2 files chiến lược**

```bash
# File 1: Feature Engineering Strategy
cat FEATURE_ENGINEERING_STRATEGY.md

# Nội dung quan trọng:
# - 40 features chia 7 nhóm
# - Mỗi feature có công thức tính toán cụ thể
# - Hardcoded dates (Tết, holidays, COVID)
# - Statistics pre-computed từ train data

# File 2: Ensemble Feature Allocation  
cat ENSEMBLE_FEATURE_ALLOCATION.md

# Nội dung quan trọng:
# - Prophet: ~5 inputs (Date + Holidays + 3 COVID regressors)
# - LightGBM: ALL 40 features
# - N-BEATS: 0 features (pure sequence)
# - Diversity strategy
```

**⚠️ CRITICAL: Đọc KỸ 2 files trước khi bắt đầu code!**

---

---

## 🎯 NHIỆM VỤ: IMPLEMENT 3 FUNCTIONS

### **Overview:**

```python
# Function 1: prepare_prophet_features()
Input:  pd.DataFrame với columns [Date, Revenue, COGS]
Output: Dict với {
    'df': DataFrame[ds, y],           # Prophet format
    'holidays': DataFrame,             # Holidays list
    'regressors': DataFrame[COVID]     # 3 COVID flags
}

# Function 2: prepare_lightgbm_features()
Input:  pd.DataFrame với columns [Date, Revenue, COGS]
        + Pre-computed statistics
Output: pd.DataFrame với 40 features + target

# Function 3: prepare_nbeats_features()
Input:  pd.DataFrame với columns [Date, Revenue, COGS]
Output: Dict với {
    'y': np.array (pure sequence),
    'dates': pd.DatetimeIndex
}
```

---

---

## 📝 FUNCTION 1: `prepare_prophet_features()`

### **Mục đích:**
Chuẩn bị data cho Prophet theo format yêu cầu:
- `ds` (date column)
- `y` (target column)  
- `holidays` (DataFrame của các ngày lễ)
- `regressors` (3 COVID flags)

---

### **Template Function:**

```python
import pandas as pd
import numpy as np
from typing import Dict, Tuple

def prepare_prophet_features(
    df: pd.DataFrame,
    target_col: str = 'Revenue'  # Hoặc 'COGS'
) -> Dict[str, pd.DataFrame]:
    """
    Chuẩn bị features cho Prophet model
    
    Args:
        df: DataFrame với columns [Date, Revenue, COGS]
        target_col: 'Revenue' hoặc 'COGS'
        
    Returns:
        Dictionary với keys:
            - 'df': Main DataFrame [ds, y]
            - 'holidays': Holidays DataFrame
            - 'regressors': COVID flags DataFrame
    """
    # ════════════════════════════════════════════════════════
    # A. MAIN DATAFRAME
    # ════════════════════════════════════════════════════════
    prophet_df = pd.DataFrame({
        'ds': pd.to_datetime(df['Date']),
        'y': df[target_col]
    })
    
    # ════════════════════════════════════════════════════════
    # B. HOLIDAYS DATAFRAME
    # ════════════════════════════════════════════════════════
    holidays = _create_holidays_dataframe()
    
    # ════════════════════════════════════════════════════════
    # C. COVID REGRESSORS
    # ════════════════════════════════════════════════════════
    regressors = _create_covid_regressors(prophet_df['ds'])
    
    return {
        'df': prophet_df,
        'holidays': holidays,
        'regressors': regressors
    }


def _create_holidays_dataframe() -> pd.DataFrame:
    """
    Tạo DataFrame chứa tất cả holidays
    
    Returns:
        DataFrame với columns [ds, holiday, lower_window, upper_window]
    """
    holidays_list = []
    
    # ────────────────────────────────────────────────────────
    # GROUP 1: TẾT NGUYÊN ĐÁN
    # ────────────────────────────────────────────────────────
    tet_dates = {
        2013: '02-10', 2014: '01-31', 2015: '02-19', 2016: '02-08',
        2017: '01-28', 2018: '02-16', 2019: '02-05', 2020: '01-25',
        2021: '02-12', 2022: '02-01', 2023: '01-22', 2024: '02-10'
    }
    
    for year, month_day in tet_dates.items():
        holidays_list.append({
            'ds': pd.Timestamp(f'{year}-{month_day}'),
            'holiday': 'tet',
            'lower_window': -21,  # 3 tuần trước
            'upper_window': 10     # Đến Mùng 10
        })
    
    # ────────────────────────────────────────────────────────
    # GROUP 2: SHOPPING FESTIVALS
    # ────────────────────────────────────────────────────────
    years = range(2012, 2025)
    
    # 11/11 - Singles Day
    for year in years:
        holidays_list.append({
            'ds': pd.Timestamp(f'{year}-11-11'),
            'holiday': '11_11',
            'lower_window': -3,
            'upper_window': 1
        })
    
    # 12/12
    for year in years:
        holidays_list.append({
            'ds': pd.Timestamp(f'{year}-12-12'),
            'holiday': '12_12',
            'lower_window': -3,
            'upper_window': 1
        })
    
    # 9/9
    for year in years:
        holidays_list.append({
            'ds': pd.Timestamp(f'{year}-09-09'),
            'holiday': '9_9',
            'lower_window': -2,
            'upper_window': 1
        })
    
    # Black Friday (Friday sau Thursday thứ 4 của November)
    for year in years:
        # Tìm Thursday thứ 4 của November
        nov_thursdays = pd.date_range(
            start=f'{year}-11-01',
            end=f'{year}-11-30',
            freq='W-THU'
        )
        if len(nov_thursdays) >= 4:
            black_friday = nov_thursdays[3] + pd.Timedelta(days=1)
            holidays_list.append({
                'ds': black_friday,
                'holiday': 'black_friday',
                'lower_window': -2,
                'upper_window': 2
            })
    
    # Cyber Monday (Monday sau Black Friday)
    for year in years:
        nov_thursdays = pd.date_range(
            start=f'{year}-11-01',
            end=f'{year}-11-30',
            freq='W-THU'
        )
        if len(nov_thursdays) >= 4:
            cyber_monday = nov_thursdays[3] + pd.Timedelta(days=4)
            holidays_list.append({
                'ds': cyber_monday,
                'holiday': 'cyber_monday',
                'lower_window': -1,
                'upper_window': 1
            })
    
    # ────────────────────────────────────────────────────────
    # GROUP 3: GIFT OCCASIONS
    # ────────────────────────────────────────────────────────
    gift_holidays = [
        ('02-14', 'valentine', -7, 0),   # Valentine
        ('03-08', 'womens_day', -7, 0),  # 8/3
        ('10-20', 'vn_womens_day', -7, 0), # 20/10
    ]
    
    for month_day, name, lower, upper in gift_holidays:
        for year in years:
            holidays_list.append({
                'ds': pd.Timestamp(f'{year}-{month_day}'),
                'holiday': name,
                'lower_window': lower,
                'upper_window': upper
            })
    
    # ────────────────────────────────────────────────────────
    # GROUP 4: TRAVEL PERIODS
    # ────────────────────────────────────────────────────────
    travel_holidays = [
        ('04-30', 'reunification', -10, 0),  # 30/4
        ('09-02', 'national_day', -10, 0),   # 2/9
    ]
    
    for month_day, name, lower, upper in travel_holidays:
        for year in years:
            holidays_list.append({
                'ds': pd.Timestamp(f'{year}-{month_day}'),
                'holiday': name,
                'lower_window': lower,
                'upper_window': upper
            })
    
    return pd.DataFrame(holidays_list)


def _create_covid_regressors(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Tạo 3 COVID flags cho Prophet regressors
    
    Args:
        dates: DatetimeIndex của data
        
    Returns:
        DataFrame với columns [is_pre_lockdown, is_lockdown, is_post_lockdown]
    """
    # Timeline Delta Wave HCMC 2021
    pre_lockdown_start = pd.Timestamp('2021-05-09')
    pre_lockdown_end = pd.Timestamp('2021-05-22')
    
    lockdown_start = pd.Timestamp('2021-05-23')
    lockdown_end = pd.Timestamp('2021-10-01')
    
    post_lockdown_start = pd.Timestamp('2021-10-02')
    post_lockdown_end = pd.Timestamp('2021-11-01')
    
    regressors = pd.DataFrame({
        'is_pre_lockdown': (
            (dates >= pre_lockdown_start) & 
            (dates <= pre_lockdown_end)
        ).astype(int),
        
        'is_lockdown': (
            (dates >= lockdown_start) & 
            (dates <= lockdown_end)
        ).astype(int),
        
        'is_post_lockdown': (
            (dates >= post_lockdown_start) & 
            (dates <= post_lockdown_end)
        ).astype(int),
    })
    
    return regressors
```

---

### **Test Function 1:**

```python
# Test với 5 dòng đầu
test_df = pd.read_csv('sales.csv', nrows=5)
test_df['Date'] = pd.to_datetime(test_df['Date'])

result = prepare_prophet_features(test_df, target_col='Revenue')

print("=" * 60)
print("PROPHET FEATURES TEST")
print("=" * 60)

print("\n1. Main DataFrame:")
print(result['df'])

print("\n2. Holidays (first 10):")
print(result['holidays'].head(10))

print("\n3. COVID Regressors:")
print(result['regressors'])

print("\n4. Summary:")
print(f"   - Main df shape: {result['df'].shape}")
print(f"   - Holidays count: {len(result['holidays'])}")
print(f"   - Regressors shape: {result['regressors'].shape}")
```

**Expected output:**
```
1. Main DataFrame:
           ds        y
0  2012-07-04  1950.89
1  2012-07-05  1534.60
2  2012-07-06  2571.86
3  2012-07-07  1518.93
4  2012-07-08  1595.85

2. Holidays (first 10):
           ds       holiday  lower_window  upper_window
0  2013-02-10           tet           -21            10
1  2014-01-31           tet           -21            10
...

3. COVID Regressors:
   is_pre_lockdown  is_lockdown  is_post_lockdown
0                0            0                 0
1                0            0                 0
2                0            0                 0
3                0            0                 0
4                0            0                 0

4. Summary:
   - Main df shape: (5, 2)
   - Holidays count: ~200
   - Regressors shape: (5, 3)
```

---

---

## 📝 FUNCTION 2: `prepare_lightgbm_features()`

### **Mục đích:**
Tạo ALL 40 features cho LightGBM từ Date column

---

### **Template Function:**

```python
def prepare_lightgbm_features(
    df: pd.DataFrame,
    statistics: Dict = None,  # Pre-computed statistics
    target_col: str = 'Revenue'
) -> pd.DataFrame:
    """
    Tạo 40 features cho LightGBM
    
    Args:
        df: DataFrame với [Date, Revenue, COGS]
        statistics: Dict chứa pre-computed statistics từ train
        target_col: 'Revenue' hoặc 'COGS'
        
    Returns:
        DataFrame với 40 features + target
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    features_df = pd.DataFrame()
    features_df['Date'] = df['Date']
    
    # ════════════════════════════════════════════════════════
    # NHÓM 1: CALENDAR & LIQUIDITY ENGINE (6 features)
    # ════════════════════════════════════════════════════════
    features_df['day_of_week'] = df['Date'].dt.dayofweek
    features_df['month'] = df['Date'].dt.month
    features_df['day_of_month'] = df['Date'].dt.day
    features_df['is_weekend'] = (df['Date'].dt.dayofweek >= 5).astype(int)
    
    # Payday window (25-31)
    features_df['is_payday_window'] = (df['Date'].dt.day >= 25).astype(int)
    
    # Distance to payday (countdown to day 28)
    features_df['dist_to_payday'] = df['Date'].apply(
        lambda d: 28 - d.day if d.day <= 28 else (
            28 + (pd.Timestamp(d.year, d.month, 1) + pd.offsets.MonthEnd(1)).day - d.day
        )
    )
    
    # ════════════════════════════════════════════════════════
    # NHÓM 2: TẾT NGUYÊN ĐÁN (5 features)
    # ════════════════════════════════════════════════════════
    tet_dates = {
        2013: '02-10', 2014: '01-31', 2015: '02-19', 2016: '02-08',
        2017: '01-28', 2018: '02-16', 2019: '02-05', 2020: '01-25',
        2021: '02-12', 2022: '02-01', 2023: '01-22', 2024: '02-10'
    }
    
    def get_days_to_tet(date):
        year = date.year
        tet = pd.Timestamp(f"{year}-{tet_dates.get(year, '01-01')}")
        days = (tet - date).days
        
        # Nếu quá xa, check Tết năm sau
        if days < -30:
            next_year = year + 1
            if next_year in tet_dates:
                tet = pd.Timestamp(f"{next_year}-{tet_dates[next_year]}")
                days = (tet - date).days
        
        return days
    
    features_df['days_to_tet'] = df['Date'].apply(get_days_to_tet)
    
    # Tet phases
    features_df['is_tet_buildup'] = (
        (features_df['days_to_tet'] >= 11) & 
        (features_df['days_to_tet'] <= 21)
    ).astype(int)
    
    features_df['is_tet_peak'] = (
        (features_df['days_to_tet'] >= 4) & 
        (features_df['days_to_tet'] <= 10)
    ).astype(int)
    
    features_df['is_tet_holiday'] = (
        (features_df['days_to_tet'] >= -3) & 
        (features_df['days_to_tet'] <= 3)
    ).astype(int)
    
    features_df['is_tet_reopening'] = (
        (features_df['days_to_tet'] >= -10) & 
        (features_df['days_to_tet'] <= -4)
    ).astype(int)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 3: FASHION SHOPPING WINDOWS (5 features)
    # ════════════════════════════════════════════════════════
    
    def is_in_gift_peak(date):
        """7-2 days before Valentine, 8/3, 20/10"""
        gift_dates = [
            pd.Timestamp(date.year, 2, 14),   # Valentine
            pd.Timestamp(date.year, 3, 8),    # 8/3
            pd.Timestamp(date.year, 10, 20),  # 20/10
        ]
        
        for gift_date in gift_dates:
            days_before = (gift_date - date).days
            if 2 <= days_before <= 7:
                return 1
        return 0
    
    def is_in_travel_peak(date):
        """10-3 days before 30/4, 2/9"""
        travel_dates = [
            pd.Timestamp(date.year, 4, 30),
            pd.Timestamp(date.year, 9, 2),
        ]
        
        for travel_date in travel_dates:
            days_before = (travel_date - date).days
            if 3 <= days_before <= 10:
                return 1
        return 0
    
    features_df['is_gift_peak'] = df['Date'].apply(is_in_gift_peak)
    features_df['is_travel_peak'] = df['Date'].apply(is_in_travel_peak)
    
    # Year-end festive (10/12 - 30/12)
    features_df['is_year_end_festive'] = (
        (df['Date'].dt.month == 12) & 
        (df['Date'].dt.day >= 10) & 
        (df['Date'].dt.day <= 30)
    ).astype(int)
    
    # Ghost month (lunar month 7 - simplified to July)
    features_df['is_ghost_month'] = (df['Date'].dt.month == 7).astype(int)
    
    # Distance to nearest holiday (simplified)
    def dist_to_nearest_holiday(date):
        holidays = [
            pd.Timestamp(date.year, 2, 14),
            pd.Timestamp(date.year, 3, 8),
            pd.Timestamp(date.year, 4, 30),
            pd.Timestamp(date.year, 9, 2),
            pd.Timestamp(date.year, 10, 20),
        ]
        dists = [(h - date).days for h in holidays]
        valid_dists = [d for d in dists if d >= 0]
        return min(valid_dists) if valid_dists else 365
    
    features_df['dist_to_nearest_holiday'] = df['Date'].apply(dist_to_nearest_holiday)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 4: E-COMMERCE SALE DAYS (5 features)
    # ════════════════════════════════════════════════════════
    
    def get_shopping_festival_score(date):
        """Ordinal 0-3"""
        month_day = (date.month, date.day)
        
        if month_day in [(11, 11), (12, 12)]:  # Mega sales
            return 3
        elif month_day in [(9, 9), (10, 10)]:   # Big sales
            return 2
        elif date.day == date.month and date.day <= 8:  # 1/1, 2/2...8/8
            return 1
        else:
            return 0
    
    features_df['shopping_festival_score'] = df['Date'].apply(get_shopping_festival_score)
    
    # Days to next big sale
    def days_to_next_big_sale(date):
        big_sales = [
            pd.Timestamp(date.year, 9, 9),
            pd.Timestamp(date.year, 10, 10),
            pd.Timestamp(date.year, 11, 11),
            pd.Timestamp(date.year, 12, 12),
        ]
        # Add Black Friday (approximate)
        # Add next year if current year passed
        if date.month == 12 and date.day > 12:
            big_sales.extend([
                pd.Timestamp(date.year + 1, 9, 9),
                pd.Timestamp(date.year + 1, 10, 10),
            ])
        
        future_sales = [s for s in big_sales if s >= date]
        if future_sales:
            return (min(future_sales) - date).days
        return 365
    
    features_df['days_to_next_big_sale'] = df['Date'].apply(days_to_next_big_sale)
    
    # Sale leadup (1-3 days before big sale)
    features_df['is_sale_leadup'] = (
        (features_df['days_to_next_big_sale'] >= 1) & 
        (features_df['days_to_next_big_sale'] <= 3)
    ).astype(int)
    
    # Black Friday & Cyber Monday (simplified)
    features_df['is_black_friday'] = 0  # TODO: Calculate actual
    features_df['is_cyber_monday'] = 0  # TODO: Calculate actual
    
    # ════════════════════════════════════════════════════════
    # NHÓM 5: HYBRID MEMORY ENGINE (14 features)
    # ════════════════════════════════════════════════════════
    
    # A. Near-term lags (2)
    features_df['rev_lag_364'] = df['Revenue'].shift(364)
    features_df['cogs_lag_364'] = df['COGS'].shift(364)
    
    # B. Safe anchor lags (4)
    features_df['rev_lag_728'] = df['Revenue'].shift(728)
    features_df['cogs_lag_728'] = df['COGS'].shift(728)
    
    # Rolling mean around lag 728
    features_df['rev_roll_mean_28_lag_728'] = (
        df['Revenue'].shift(728).rolling(28, center=True, min_periods=1).mean()
    )
    features_df['cogs_roll_mean_28_lag_728'] = (
        df['COGS'].shift(728).rolling(28, center=True, min_periods=1).mean()
    )
    
    # C. Statistics (8) - Use pre-computed if available
    if statistics is None:
        # Compute on-the-fly (for testing)
        statistics = _compute_statistics(df)
    
    # Lookup statistics
    features_df['stat_rev_mean_dow_month'] = features_df.apply(
        lambda row: statistics['rev_mean_dow_month'].get(
            (row['day_of_week'], row['month']), 
            df['Revenue'].mean()
        ), axis=1
    )
    
    features_df['stat_cogs_mean_dow_month'] = features_df.apply(
        lambda row: statistics['cogs_mean_dow_month'].get(
            (row['day_of_week'], row['month']), 
            df['COGS'].mean()
        ), axis=1
    )
    
    features_df['stat_rev_std_month'] = features_df['month'].map(
        statistics['rev_std_month']
    ).fillna(df['Revenue'].std())
    
    features_df['stat_cogs_std_month'] = features_df['month'].map(
        statistics['cogs_std_month']
    ).fillna(df['COGS'].std())
    
    features_df['stat_rev_median_day'] = features_df['day_of_month'].map(
        statistics['rev_median_day']
    ).fillna(df['Revenue'].median())
    
    features_df['stat_cogs_median_day'] = features_df['day_of_month'].map(
        statistics['cogs_median_day']
    ).fillna(df['COGS'].median())
    
    features_df['stat_rev_yoy_growth_month'] = features_df['month'].map(
        statistics['rev_yoy_growth_month']
    ).fillna(0)
    
    features_df['stat_cogs_yoy_growth_month'] = features_df['month'].map(
        statistics['cogs_yoy_growth_month']
    ).fillna(0)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 6: FOURIER FEATURES (2 features)
    # ════════════════════════════════════════════════════════
    day_of_year = df['Date'].dt.dayofyear
    features_df['sin_annual_1'] = np.sin(2 * np.pi * day_of_year / 365.25)
    features_df['cos_annual_1'] = np.cos(2 * np.pi * day_of_year / 365.25)
    
    # ════════════════════════════════════════════════════════
    # NHÓM 7: COVID-19 (3 features)
    # ════════════════════════════════════════════════════════
    features_df['is_pre_lockdown'] = (
        (df['Date'] >= '2021-05-09') & 
        (df['Date'] <= '2021-05-22')
    ).astype(int)
    
    features_df['is_lockdown'] = (
        (df['Date'] >= '2021-05-23') & 
        (df['Date'] <= '2021-10-01')
    ).astype(int)
    
    features_df['is_post_lockdown'] = (
        (df['Date'] >= '2021-10-02') & 
        (df['Date'] <= '2021-11-01')
    ).astype(int)
    
    # ════════════════════════════════════════════════════════
    # ADD TARGET
    # ════════════════════════════════════════════════════════
    features_df['target'] = df[target_col]
    
    return features_df


def _compute_statistics(df: pd.DataFrame) -> Dict:
    """
    Compute statistics từ training data
    (Đây là simplified version cho testing)
    """
    df['day_of_week'] = df['Date'].dt.dayofweek
    df['month'] = df['Date'].dt.month
    df['day'] = df['Date'].dt.day
    
    stats = {
        'rev_mean_dow_month': df.groupby(['day_of_week', 'month'])['Revenue'].mean().to_dict(),
        'cogs_mean_dow_month': df.groupby(['day_of_week', 'month'])['COGS'].mean().to_dict(),
        'rev_std_month': df.groupby('month')['Revenue'].std().to_dict(),
        'cogs_std_month': df.groupby('month')['COGS'].std().to_dict(),
        'rev_median_day': df.groupby('day')['Revenue'].median().to_dict(),
        'cogs_median_day': df.groupby('day')['COGS'].median().to_dict(),
        'rev_yoy_growth_month': {m: 0.1 for m in range(1, 13)},  # Simplified
        'cogs_yoy_growth_month': {m: 0.08 for m in range(1, 13)},  # Simplified
    }
    
    return stats
```

---

### **Test Function 2:**

```python
# Test với 5 dòng đầu
test_df = pd.read_csv('sales.csv', nrows=5)

lgbm_features = prepare_lightgbm_features(test_df, target_col='Revenue')

print("=" * 60)
print("LIGHTGBM FEATURES TEST")
print("=" * 60)

print("\n1. Feature columns (should be 40 + Date + target):")
print(f"   Total columns: {len(lgbm_features.columns)}")
print(f"   Columns: {list(lgbm_features.columns)}")

print("\n2. First row values:")
print(lgbm_features.iloc[0])

print("\n3. Feature groups check:")
print(f"   Calendar (6): day_of_week, month, day_of_month, is_weekend, is_payday_window, dist_to_payday")
print(f"   Tết (5): days_to_tet, is_tet_buildup, is_tet_peak, is_tet_holiday, is_tet_reopening")
print(f"   Fashion (5): is_gift_peak, is_travel_peak, is_year_end_festive, is_ghost_month, dist_to_nearest_holiday")
print(f"   E-commerce (5): shopping_festival_score, days_to_next_big_sale, is_sale_leadup, is_black_friday, is_cyber_monday")
print(f"   Memory (14): lag_364, lag_728, roll_mean, statistics (8)")
print(f"   Fourier (2): sin_annual_1, cos_annual_1")
print(f"   COVID (3): is_pre_lockdown, is_lockdown, is_post_lockdown")

print("\n4. Check for NaN in first 5 rows:")
print(lgbm_features.isnull().sum()[lgbm_features.isnull().sum() > 0])
```

**Expected output:**
```
LIGHTGBM FEATURES TEST
==================================================

1. Feature columns (should be 40 + Date + target):
   Total columns: 43
   Columns: ['Date', 'day_of_week', 'month', ..., 'target']

2. First row values:
Date                       2012-07-04
day_of_week                         2
month                               7
...
target                        1950.89
Name: 0, dtype: object

3. Feature groups check:
   [As listed above]

4. Check for NaN in first 5 rows:
   rev_lag_364                 5
   cogs_lag_364                5
   rev_lag_728                 5
   cogs_lag_728                5
   (Expected - not enough history for lags)
```

---

---

## 📝 FUNCTION 3: `prepare_nbeats_features()`

### **Mục đích:**
Chuẩn bị pure sequence cho N-BEATS (NO features!)

---

### **Template Function:**

```python
def prepare_nbeats_features(
    df: pd.DataFrame,
    target_col: str = 'Revenue'
) -> Dict[str, np.ndarray]:
    """
    Chuẩn bị pure sequence cho N-BEATS
    
    Args:
        df: DataFrame với [Date, Revenue, COGS]
        target_col: 'Revenue' hoặc 'COGS'
        
    Returns:
        Dict với:
            - 'y': np.array (pure time series)
            - 'dates': pd.DatetimeIndex
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    return {
        'y': df[target_col].values,
        'dates': pd.DatetimeIndex(df['Date'])
    }
```

---

### **Test Function 3:**

```python
# Test với 5 dòng đầu
test_df = pd.read_csv('sales.csv', nrows=5)

nbeats_data = prepare_nbeats_features(test_df, target_col='Revenue')

print("=" * 60)
print("N-BEATS FEATURES TEST")
print("=" * 60)

print("\n1. Pure sequence (y):")
print(f"   Type: {type(nbeats_data['y'])}")
print(f"   Shape: {nbeats_data['y'].shape}")
print(f"   Values: {nbeats_data['y']}")

print("\n2. Dates:")
print(f"   Type: {type(nbeats_data['dates'])}")
print(f"   Values: {nbeats_data['dates']}")

print("\n3. Confirm NO FEATURES:")
print(f"   Keys in output: {list(nbeats_data.keys())}")
print(f"   Expected: ['y', 'dates'] only ✓")

print("\n4. Sequence stats:")
print(f"   Min: {nbeats_data['y'].min():.2f}")
print(f"   Max: {nbeats_data['y'].max():.2f}")
print(f"   Mean: {nbeats_data['y'].mean():.2f}")
print(f"   Std: {nbeats_data['y'].std():.2f}")
```

**Expected output:**
```
N-BEATS FEATURES TEST
==================================================

1. Pure sequence (y):
   Type: <class 'numpy.ndarray'>
   Shape: (5,)
   Values: [1950.89 1534.6  2571.86 1518.93 1595.85]

2. Dates:
   Type: <class 'pandas.core.indexes.datetimes.DatetimeIndex'>
   Values: DatetimeIndex(['2012-07-04', '2012-07-05', '2012-07-06',
                          '2012-07-07', '2012-07-08'],
                         dtype='datetime64[ns]', freq=None)

3. Confirm NO FEATURES:
   Keys in output: ['y', 'dates']
   Expected: ['y', 'dates'] only ✓

4. Sequence stats:
   Min: 1518.93
   Max: 2571.86
   Mean: 1834.43
   Std: 427.42
```

---

---

## ✅ FINAL VERIFICATION SCRIPT

### **Chạy tất cả tests cùng lúc:**

```python
import pandas as pd
import numpy as np

def run_all_tests():
    """
    Test cả 3 functions với 5 dòng đầu của sales.csv
    """
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "3-FUNCTION VERIFICATION TEST" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Load test data
    test_df = pd.read_csv('sales.csv', nrows=5)
    test_df['Date'] = pd.to_datetime(test_df['Date'])
    
    print("\n📊 Test Data (first 5 rows):")
    print(test_df)
    print(f"\nShape: {test_df.shape}")
    
    # ════════════════════════════════════════════════════════
    # TEST 1: PROPHET
    # ════════════════════════════════════════════════════════
    print("\n\n" + "─" * 60)
    print("TEST 1: PROPHET FEATURES")
    print("─" * 60)
    
    try:
        prophet_result = prepare_prophet_features(test_df, target_col='Revenue')
        
        print("✓ Prophet features created successfully")
        print(f"  - Main df shape: {prophet_result['df'].shape}")
        print(f"  - Holidays count: {len(prophet_result['holidays'])}")
        print(f"  - Regressors shape: {prophet_result['regressors'].shape}")
        print(f"\n  Main df preview:")
        print(prophet_result['df'].head(3))
        
    except Exception as e:
        print(f"✗ Prophet test FAILED: {e}")
    
    # ════════════════════════════════════════════════════════
    # TEST 2: LIGHTGBM
    # ════════════════════════════════════════════════════════
    print("\n\n" + "─" * 60)
    print("TEST 2: LIGHTGBM FEATURES")
    print("─" * 60)
    
    try:
        lgbm_result = prepare_lightgbm_features(test_df, target_col='Revenue')
        
        print("✓ LightGBM features created successfully")
        print(f"  - Total columns: {len(lgbm_result.columns)}")
        print(f"  - Shape: {lgbm_result.shape}")
        print(f"  - Expected: (5 rows, 43 cols) [40 features + Date + target]")
        
        # Count features by group
        calendar_features = ['day_of_week', 'month', 'day_of_month', 
                            'is_weekend', 'is_payday_window', 'dist_to_payday']
        print(f"\n  Feature groups present:")
        print(f"    Calendar: {sum(1 for f in calendar_features if f in lgbm_result.columns)}/6")
        
        # Check for NaN
        nan_count = lgbm_result.isnull().sum().sum()
        print(f"  - Total NaN values: {nan_count} (expected: 20 from lag features)")
        
    except Exception as e:
        print(f"✗ LightGBM test FAILED: {e}")
    
    # ════════════════════════════════════════════════════════
    # TEST 3: N-BEATS
    # ════════════════════════════════════════════════════════
    print("\n\n" + "─" * 60)
    print("TEST 3: N-BEATS FEATURES")
    print("─" * 60)
    
    try:
        nbeats_result = prepare_nbeats_features(test_df, target_col='Revenue')
        
        print("✓ N-BEATS features created successfully")
        print(f"  - Sequence shape: {nbeats_result['y'].shape}")
        print(f"  - Dates count: {len(nbeats_result['dates'])}")
        print(f"  - Keys: {list(nbeats_result.keys())}")
        print(f"  - NO FEATURES: {len(nbeats_result.keys()) == 2}")
        print(f"\n  Sequence preview:")
        print(f"    {nbeats_result['y']}")
        
    except Exception as e:
        print(f"✗ N-BEATS test FAILED: {e}")
    
    # ════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════
    print("\n\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "TEST SUMMARY" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    
    print("\n✓ All 3 functions executed")
    print("✓ Ready for full dataset implementation")
    print("\nNext steps:")
    print("  1. Run with full sales.csv")
    print("  2. Pre-compute statistics for LightGBM")
    print("  3. Implement iterative prediction for test set")
    print("  4. Train 3 models with prepared features")


# RUN
if __name__ == "__main__":
    run_all_tests()
```

---

---

## 📋 CHECKLIST CHO CLAUDE CODE

```
☐ Đọc FEATURE_ENGINEERING_STRATEGY.md
☐ Đọc ENSEMBLE_FEATURE_ALLOCATION.md

☐ Implement prepare_prophet_features()
  ☐ Main DataFrame (ds, y)
  ☐ Holidays DataFrame (~200 rows)
  ☐ COVID regressors (3 flags)

☐ Implement prepare_lightgbm_features()
  ☐ Nhóm 1: Calendar (6 features)
  ☐ Nhóm 2: Tết (5 features)
  ☐ Nhóm 3: Fashion (5 features)
  ☐ Nhóm 4: E-commerce (5 features)
  ☐ Nhóm 5: Memory (14 features)
  ☐ Nhóm 6: Fourier (2 features)
  ☐ Nhóm 7: COVID (3 features)
  ☐ Total: 40 features + target

☐ Implement prepare_nbeats_features()
  ☐ Pure sequence (y array)
  ☐ Dates (DatetimeIndex)
  ☐ NO features

☐ Test với 5 dòng đầu sales.csv
  ☐ Prophet test pass
  ☐ LightGBM test pass (40 features)
  ☐ N-BEATS test pass (0 features)

☐ Verify diversity:
  ☐ Prophet: ~5 inputs
  ☐ LightGBM: 40 features
  ☐ N-BEATS: 0 features
  ☐ Diversity ≈ 75% ✓
```

---

## 🎯 SUCCESS CRITERIA

**3 functions đạt chuẩn khi:**

1. ✅ **Prophet:**
   - Output có 3 keys: 'df', 'holidays', 'regressors'
   - Main df shape: (n, 2) với columns [ds, y]
   - Holidays count: ~200 rows
   - Regressors shape: (n, 3)

2. ✅ **LightGBM:**
   - Output có ĐÚNG 43 columns (40 features + Date + target)
   - Tất cả 7 nhóm features đều có
   - NaN chỉ xuất hiện ở lag features (expected)

3. ✅ **N-BEATS:**
   - Output có ĐÚNG 2 keys: 'y', 'dates'
   - y là numpy array
   - dates là DatetimeIndex
   - Không có features nào khác

**Khi cả 3 pass → Sẵn sàng implement với full dataset!**

---

**File này để hướng dẫn Claude Code viết code! 🚀**
