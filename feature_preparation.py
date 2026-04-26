from __future__ import annotations

import calendar
import math
from typing import Dict

import numpy as np
import pandas as pd


TET_DATES = {
    2013: pd.Timestamp("2013-02-10"),
    2014: pd.Timestamp("2014-01-31"),
    2015: pd.Timestamp("2015-02-19"),
    2016: pd.Timestamp("2016-02-08"),
    2017: pd.Timestamp("2017-01-28"),
    2018: pd.Timestamp("2018-02-16"),
    2019: pd.Timestamp("2019-02-05"),
    2020: pd.Timestamp("2020-01-25"),
    2021: pd.Timestamp("2021-02-12"),
    2022: pd.Timestamp("2022-02-01"),
    2023: pd.Timestamp("2023-01-22"),
    2024: pd.Timestamp("2024-02-10"),
}

HOLIDAY_YEARS = range(2012, 2025)
COVID_WINDOWS = {
    "is_pre_lockdown": (pd.Timestamp("2021-05-09"), pd.Timestamp("2021-05-22")),
    "is_lockdown": (pd.Timestamp("2021-05-23"), pd.Timestamp("2021-10-01")),
    "is_post_lockdown": (pd.Timestamp("2021-10-02"), pd.Timestamp("2021-11-01")),
}
LIGHTGBM_FEATURE_COLUMNS = [
    "day_of_week",
    "month",
    "day_of_month",
    "is_payday_window",
    "dist_to_payday",
    "is_weekend",
    "days_to_tet",
    "is_tet_buildup",
    "is_tet_peak",
    "is_tet_holiday",
    "is_tet_reopening",
    "is_gift_peak",
    "is_travel_peak",
    "is_year_end_festive",
    "is_ghost_month",
    "dist_to_nearest_holiday",
    "shopping_festival_score",
    "days_to_next_big_sale",
    "is_sale_leadup",
    "is_black_friday",
    "is_cyber_monday",
    "rev_lag_364",
    "cogs_lag_364",
    "rev_lag_728",
    "cogs_lag_728",
    "rev_roll_mean_28_lag_728",
    "cogs_roll_mean_28_lag_728",
    "stat_rev_mean_dow_month",
    "stat_cogs_mean_dow_month",
    "stat_rev_std_month",
    "stat_cogs_std_month",
    "stat_rev_median_day",
    "stat_cogs_median_day",
    "stat_rev_yoy_growth_month",
    "stat_cogs_yoy_growth_month",
    "sin_annual_1",
    "cos_annual_1",
    "is_pre_lockdown",
    "is_lockdown",
    "is_post_lockdown",
]


def prepare_prophet_features(
    df: pd.DataFrame,
    target_col: str = "Revenue",
) -> Dict[str, pd.DataFrame]:
    base = _prepare_base_frame(df, target_col=target_col)
    prophet_df = base.rename(columns={"Date": "ds", target_col: "y"})[["ds", "y"]]
    regressors = _create_covid_regressors(prophet_df["ds"])
    return {
        "df": prophet_df,
        "holidays": _create_holidays_dataframe(),
        "regressors": regressors,
    }


def prepare_lightgbm_features(
    df: pd.DataFrame,
    statistics: Dict | None = None,
    target_col: str = "Revenue",
) -> pd.DataFrame:
    base = _prepare_base_frame(df, target_col=target_col)
    features = pd.DataFrame({"Date": base["Date"]})

    dates = base["Date"]
    features["day_of_week"] = dates.dt.dayofweek
    features["month"] = dates.dt.month
    features["day_of_month"] = dates.dt.day
    features["is_payday_window"] = (features["day_of_month"] >= 25).astype(int)
    features["dist_to_payday"] = dates.apply(_calc_dist_to_payday)
    features["is_weekend"] = (features["day_of_week"] >= 5).astype(int)

    features["days_to_tet"] = dates.apply(_calc_days_to_tet)
    features["is_tet_buildup"] = features["days_to_tet"].between(-21, -11).astype(int)
    features["is_tet_peak"] = features["days_to_tet"].between(-10, -4).astype(int)
    features["is_tet_holiday"] = features["days_to_tet"].between(-3, 3).astype(int)
    features["is_tet_reopening"] = features["days_to_tet"].between(4, 10).astype(int)

    features["is_gift_peak"] = dates.apply(_is_gift_peak).astype(int)
    features["is_travel_peak"] = dates.apply(_is_travel_peak).astype(int)
    features["is_year_end_festive"] = (
        (dates.dt.month == 12) & dates.dt.day.between(10, 30)
    ).astype(int)
    features["is_ghost_month"] = dates.apply(_is_ghost_month).astype(int)
    features["dist_to_nearest_holiday"] = dates.apply(_calc_dist_to_nearest_holiday)

    features["shopping_festival_score"] = dates.apply(_calc_shopping_festival_score)
    features["days_to_next_big_sale"] = dates.apply(_calc_days_to_next_big_sale)
    features["is_sale_leadup"] = features["days_to_next_big_sale"].between(1, 3).astype(int)
    features["is_black_friday"] = dates.apply(_is_black_friday).astype(int)
    features["is_cyber_monday"] = dates.apply(_is_cyber_monday).astype(int)

    features["rev_lag_364"] = base["Revenue"].shift(364)
    features["cogs_lag_364"] = base["COGS"].shift(364)
    features["rev_lag_728"] = base["Revenue"].shift(728)
    features["cogs_lag_728"] = base["COGS"].shift(728)
    features["rev_roll_mean_28_lag_728"] = (
        base["Revenue"].shift(728).rolling(window=28, center=True, min_periods=1).mean()
    )
    features["cogs_roll_mean_28_lag_728"] = (
        base["COGS"].shift(728).rolling(window=28, center=True, min_periods=1).mean()
    )

    stats = statistics or _compute_statistics(base)
    rev_mean_default = float(base["Revenue"].mean())
    cogs_mean_default = float(base["COGS"].mean())
    rev_std_default = _safe_float(base["Revenue"].std(), default=0.0)
    cogs_std_default = _safe_float(base["COGS"].std(), default=0.0)
    rev_median_default = float(base["Revenue"].median())
    cogs_median_default = float(base["COGS"].median())

    features["stat_rev_mean_dow_month"] = features.apply(
        lambda row: stats["rev_mean_dow_month"].get((row["day_of_week"], row["month"]), rev_mean_default),
        axis=1,
    )
    features["stat_cogs_mean_dow_month"] = features.apply(
        lambda row: stats["cogs_mean_dow_month"].get((row["day_of_week"], row["month"]), cogs_mean_default),
        axis=1,
    )
    features["stat_rev_std_month"] = features["month"].map(stats["rev_std_month"]).fillna(rev_std_default)
    features["stat_cogs_std_month"] = features["month"].map(stats["cogs_std_month"]).fillna(cogs_std_default)
    features["stat_rev_median_day"] = features["day_of_month"].map(stats["rev_median_day"]).fillna(rev_median_default)
    features["stat_cogs_median_day"] = features["day_of_month"].map(stats["cogs_median_day"]).fillna(cogs_median_default)
    features["stat_rev_yoy_growth_month"] = features["month"].map(stats["rev_yoy_growth_month"]).fillna(0.0)
    features["stat_cogs_yoy_growth_month"] = features["month"].map(stats["cogs_yoy_growth_month"]).fillna(0.0)

    day_of_year = dates.dt.dayofyear
    features["sin_annual_1"] = np.sin(2 * np.pi * day_of_year / 365.25)
    features["cos_annual_1"] = np.cos(2 * np.pi * day_of_year / 365.25)

    regressors = _create_covid_regressors(dates)
    for column in regressors.columns:
        features[column] = regressors[column].values

    features["target"] = base[target_col].values
    return features[["Date", *LIGHTGBM_FEATURE_COLUMNS, "target"]]


def prepare_nbeats_features(
    df: pd.DataFrame,
    target_col: str = "Revenue",
) -> Dict[str, np.ndarray | pd.DatetimeIndex]:
    base = _prepare_base_frame(df, target_col=target_col)
    return {
        "y": base[target_col].to_numpy(),
        "dates": pd.DatetimeIndex(base["Date"]),
    }


def _prepare_base_frame(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    required = {"Date", "Revenue", "COGS", target_col}
    missing = required.difference(df.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    base = df.copy()
    base["Date"] = pd.to_datetime(base["Date"])
    base = base.sort_values("Date").reset_index(drop=True)
    return base


def _create_holidays_dataframe() -> pd.DataFrame:
    holidays: list[dict[str, object]] = []

    for tet_date in TET_DATES.values():
        holidays.append(
            {
                "ds": tet_date,
                "holiday": "tet",
                "lower_window": -21,
                "upper_window": 10,
            }
        )

    for year in HOLIDAY_YEARS:
        holidays.extend(
            [
                {"ds": pd.Timestamp(year=year, month=11, day=11), "holiday": "11_11", "lower_window": -3, "upper_window": 1},
                {"ds": pd.Timestamp(year=year, month=12, day=12), "holiday": "12_12", "lower_window": -3, "upper_window": 1},
                {"ds": pd.Timestamp(year=year, month=9, day=9), "holiday": "9_9", "lower_window": -2, "upper_window": 1},
                {"ds": _get_black_friday(year), "holiday": "black_friday", "lower_window": -2, "upper_window": 2},
                {"ds": _get_cyber_monday(year), "holiday": "cyber_monday", "lower_window": -1, "upper_window": 1},
                {"ds": pd.Timestamp(year=year, month=2, day=14), "holiday": "valentine", "lower_window": -7, "upper_window": 0},
                {"ds": pd.Timestamp(year=year, month=3, day=8), "holiday": "womens_day", "lower_window": -7, "upper_window": 0},
                {"ds": pd.Timestamp(year=year, month=10, day=20), "holiday": "vn_womens_day", "lower_window": -7, "upper_window": 0},
                {"ds": pd.Timestamp(year=year, month=4, day=30), "holiday": "reunification", "lower_window": -10, "upper_window": 0},
                {"ds": pd.Timestamp(year=year, month=9, day=2), "holiday": "national_day", "lower_window": -10, "upper_window": 0},
            ]
        )

    return pd.DataFrame(holidays).sort_values(["ds", "holiday"]).reset_index(drop=True)


def _create_covid_regressors(dates: pd.Series | pd.DatetimeIndex) -> pd.DataFrame:
    series = pd.Series(pd.to_datetime(dates), index=getattr(dates, "index", None))
    regressors = {}
    for column, (start, end) in COVID_WINDOWS.items():
        regressors[column] = series.between(start, end).astype(int).to_numpy()
    return pd.DataFrame(regressors, index=series.index)


def _calc_dist_to_payday(date: pd.Timestamp, payday: int = 28) -> int:
    if date.day <= payday:
        return payday - date.day
    days_in_month = calendar.monthrange(date.year, date.month)[1]
    return (days_in_month - date.day) + payday


def _calc_days_to_tet(date: pd.Timestamp) -> int:
    tet_candidates = [tet_date for tet_date in TET_DATES.values() if abs((date - tet_date).days) <= 366]
    if not tet_candidates:
        tet_candidates = list(TET_DATES.values())
    closest_tet = min(tet_candidates, key=lambda tet_date: abs((date - tet_date).days))
    return (date - closest_tet).days


def _is_gift_peak(date: pd.Timestamp) -> bool:
    for month, day in ((2, 14), (3, 8), (10, 20)):
        days_until = (pd.Timestamp(year=date.year, month=month, day=day) - date).days
        if 2 <= days_until <= 7:
            return True
    return False


def _is_travel_peak(date: pd.Timestamp) -> bool:
    for month, day in ((4, 30), (9, 2)):
        days_until = (pd.Timestamp(year=date.year, month=month, day=day) - date).days
        if 3 <= days_until <= 10:
            return True
    return False


def _is_ghost_month(date: pd.Timestamp) -> bool:
    _, lunar_month, _, _ = _convert_solar_to_lunar(date.day, date.month, date.year, time_zone=7.0)
    return lunar_month == 7


def _calc_dist_to_nearest_holiday(date: pd.Timestamp) -> int:
    events = [(1, 1), (2, 14), (3, 8), (4, 30), (9, 2), (10, 20), (12, 24)]
    distances = []
    for month, day in events:
        candidate = pd.Timestamp(year=date.year, month=month, day=day)
        if candidate < date:
            candidate = pd.Timestamp(year=date.year + 1, month=month, day=day)
        distances.append((candidate - date).days)
    return min(distances)


def _calc_shopping_festival_score(date: pd.Timestamp) -> int:
    month_day = (date.month, date.day)
    if month_day in {(11, 11), (12, 12)}:
        return 3
    if month_day in {(9, 9), (10, 10)}:
        return 2
    if date.month == date.day and 1 <= date.day <= 8:
        return 1
    return 0


def _calc_days_to_next_big_sale(date: pd.Timestamp) -> int:
    sales = [
        pd.Timestamp(year=date.year, month=9, day=9),
        pd.Timestamp(year=date.year, month=10, day=10),
        pd.Timestamp(year=date.year, month=11, day=11),
        pd.Timestamp(year=date.year, month=12, day=12),
        _get_black_friday(date.year),
        _get_cyber_monday(date.year),
    ]
    future_sales = [sale_date for sale_date in sales if sale_date >= date]
    if future_sales:
        return min((sale_date - date).days for sale_date in future_sales)

    next_year_sales = [
        pd.Timestamp(year=date.year + 1, month=9, day=9),
        pd.Timestamp(year=date.year + 1, month=10, day=10),
        pd.Timestamp(year=date.year + 1, month=11, day=11),
        pd.Timestamp(year=date.year + 1, month=12, day=12),
        _get_black_friday(date.year + 1),
        _get_cyber_monday(date.year + 1),
    ]
    return min((sale_date - date).days for sale_date in next_year_sales)


def _is_black_friday(date: pd.Timestamp) -> bool:
    return date.normalize() == _get_black_friday(date.year)


def _is_cyber_monday(date: pd.Timestamp) -> bool:
    return date.normalize() == _get_cyber_monday(date.year)


def _get_black_friday(year: int) -> pd.Timestamp:
    first_day = pd.Timestamp(year=year, month=11, day=1)
    days_until_thursday = (3 - first_day.dayofweek) % 7
    first_thursday = first_day + pd.Timedelta(days=days_until_thursday)
    fourth_thursday = first_thursday + pd.Timedelta(days=21)
    return fourth_thursday + pd.Timedelta(days=1)


def _get_cyber_monday(year: int) -> pd.Timestamp:
    return _get_black_friday(year) + pd.Timedelta(days=3)


def _compute_statistics(df: pd.DataFrame) -> Dict[str, dict]:
    base = df.copy()
    base["day_of_week"] = base["Date"].dt.dayofweek
    base["month"] = base["Date"].dt.month
    base["day_of_month"] = base["Date"].dt.day

    return {
        "rev_mean_dow_month": base.groupby(["day_of_week", "month"])["Revenue"].mean().to_dict(),
        "cogs_mean_dow_month": base.groupby(["day_of_week", "month"])["COGS"].mean().to_dict(),
        "rev_std_month": base.groupby("month")["Revenue"].std().fillna(0.0).to_dict(),
        "cogs_std_month": base.groupby("month")["COGS"].std().fillna(0.0).to_dict(),
        "rev_median_day": base.groupby("day_of_month")["Revenue"].median().to_dict(),
        "cogs_median_day": base.groupby("day_of_month")["COGS"].median().to_dict(),
        "rev_yoy_growth_month": _calc_yoy_growth(base, "Revenue"),
        "cogs_yoy_growth_month": _calc_yoy_growth(base, "COGS"),
    }


def _calc_yoy_growth(df: pd.DataFrame, value_col: str) -> dict[int, float]:
    monthly = (
        df.assign(year=df["Date"].dt.year, month=df["Date"].dt.month)
        .groupby(["year", "month"])[value_col]
        .mean()
        .reset_index()
    )
    pivot = monthly.pivot(index="month", columns="year", values=value_col).sort_index(axis=1)
    yoy = pivot.pct_change(axis=1, fill_method=None).replace([np.inf, -np.inf], np.nan)
    averages = yoy.mean(axis=1).fillna(0.0)
    return {int(month): float(value) for month, value in averages.items()}


def _safe_float(value: float, default: float = 0.0) -> float:
    return default if pd.isna(value) else float(value)


def _jd_from_date(day: int, month: int, year: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - (y // 100) + (y // 400) - 32045
    if jd < 2299161:
        jd = day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - 32083
    return jd


def _get_new_moon_day(k: int, time_zone: float) -> int:
    return int(_new_moon(k) + 0.5 + time_zone / 24.0)


def _new_moon(k: int) -> float:
    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    dr = math.pi / 180.0
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * t2 - 0.000000155 * t3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * t - 0.009173 * t2) * dr)
    m = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3
    m_prime = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3
    f = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3
    c1 = (0.1734 - 0.000393 * t) * math.sin(m * dr) + 0.0021 * math.sin(2 * dr * m)
    c1 -= 0.4068 * math.sin(m_prime * dr) + 0.0161 * math.sin(dr * 2 * m_prime)
    c1 -= 0.0004 * math.sin(dr * 3 * m_prime)
    c1 += 0.0104 * math.sin(dr * 2 * f) - 0.0051 * math.sin(dr * (m + m_prime))
    c1 -= 0.0074 * math.sin(dr * (m - m_prime)) + 0.0004 * math.sin(dr * (2 * f + m))
    c1 -= 0.0004 * math.sin(dr * (2 * f - m)) - 0.0006 * math.sin(dr * (2 * f + m_prime))
    c1 += 0.0010 * math.sin(dr * (2 * f - m_prime)) + 0.0005 * math.sin(dr * (2 * m_prime + m))
    if t < -11:
        delta_t = 0.001 + 0.000839 * t + 0.0002261 * t2 - 0.00000845 * t3 - 0.000000081 * t * t3
    else:
        delta_t = -0.000278 + 0.000265 * t + 0.000262 * t2
    return jd1 + c1 - delta_t


def _get_sun_longitude(day_number: int, time_zone: float) -> int:
    t = (day_number - 2451545.5 - time_zone / 24.0) / 36525
    t2 = t * t
    dr = math.pi / 180.0
    m = 357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t * t2
    l0 = 280.46645 + 36000.76983 * t + 0.0003032 * t2
    delta_l = (1.914600 - 0.004817 * t - 0.000014 * t2) * math.sin(dr * m)
    delta_l += (0.019993 - 0.000101 * t) * math.sin(dr * 2 * m) + 0.000290 * math.sin(dr * 3 * m)
    l = (l0 + delta_l) * dr
    l = l - math.pi * 2 * math.floor(l / (math.pi * 2))
    return int(l / math.pi * 6)


def _get_lunar_month_11(year: int, time_zone: float) -> int:
    off = _jd_from_date(31, 12, year) - 2415021
    k = int(off / 29.530588853)
    new_moon = _get_new_moon_day(k, time_zone)
    if _get_sun_longitude(new_moon, time_zone) >= 9:
        new_moon = _get_new_moon_day(k - 1, time_zone)
    return new_moon


def _get_leap_month_offset(a11: int, time_zone: float) -> int:
    k = int(0.5 + (a11 - 2415021.076998695) / 29.530588853)
    last = 0
    i = 1
    arc = _get_sun_longitude(_get_new_moon_day(k + i, time_zone), time_zone)
    while arc != last and i < 14:
        last = arc
        i += 1
        arc = _get_sun_longitude(_get_new_moon_day(k + i, time_zone), time_zone)
    return i - 1


def _convert_solar_to_lunar(day: int, month: int, year: int, time_zone: float = 7.0) -> tuple[int, int, int, int]:
    day_number = _jd_from_date(day, month, year)
    k = int((day_number - 2415021.076998695) / 29.530588853)
    month_start = _get_new_moon_day(k + 1, time_zone)
    if month_start > day_number:
        month_start = _get_new_moon_day(k, time_zone)

    a11 = _get_lunar_month_11(year, time_zone)
    b11 = a11
    if a11 >= month_start:
        lunar_year = year
        a11 = _get_lunar_month_11(year - 1, time_zone)
    else:
        lunar_year = year + 1
        b11 = _get_lunar_month_11(year + 1, time_zone)

    lunar_day = day_number - month_start + 1
    diff = int((month_start - a11) / 29)
    lunar_month = diff + 11
    lunar_leap = 0

    if b11 - a11 > 365:
        leap_month_diff = _get_leap_month_offset(a11, time_zone)
        if diff >= leap_month_diff:
            lunar_month = diff + 10
            if diff == leap_month_diff:
                lunar_leap = 1

    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1

    return lunar_day, lunar_month, lunar_year, lunar_leap
