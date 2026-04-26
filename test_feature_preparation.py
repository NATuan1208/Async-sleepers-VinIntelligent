from __future__ import annotations

import pandas as pd

from feature_preparation import (
    LIGHTGBM_FEATURE_COLUMNS,
    prepare_lightgbm_features,
    prepare_nbeats_features,
    prepare_prophet_features,
)


DATA_PATH = "data/sales.csv"
N_TEST_ROWS = 22
TARGET_COL = "Revenue"


def main() -> None:
    full_df = pd.read_csv(DATA_PATH)
    test_df = full_df.tail(N_TEST_ROWS).reset_index(drop=True)

    prophet = prepare_prophet_features(test_df, target_col=TARGET_COL)
    nbeats = prepare_nbeats_features(test_df, target_col=TARGET_COL)
    lightgbm_full = prepare_lightgbm_features(full_df, target_col=TARGET_COL)
    lightgbm = lightgbm_full.tail(N_TEST_ROWS).reset_index(drop=True)

    print("=" * 72)
    print(f"FEATURE PREPARATION TEST - LAST {N_TEST_ROWS} ROWS OF {DATA_PATH}")
    print("=" * 72)

    print("\nTest window:")
    print(f"Rows used: {len(test_df)}")
    print(f"Date range: {test_df['Date'].iloc[0]} -> {test_df['Date'].iloc[-1]}")

    print("\nProphet:")
    print(f"df shape: {prophet['df'].shape}")
    print(f"holidays shape: {prophet['holidays'].shape}")
    print(f"regressors shape: {prophet['regressors'].shape}")
    print(f"first row: {prophet['df'].iloc[0].to_dict()}")
    print(f"last row: {prophet['df'].iloc[-1].to_dict()}")
    print(f"first regressor row: {prophet['regressors'].iloc[0].to_dict()}")

    print("\nLightGBM:")
    print(f"shape: {lightgbm.shape}")
    print(f"feature count: {len(LIGHTGBM_FEATURE_COLUMNS)}")
    print("feature generation scope: full sales history, then tail(22) for inspection")
    print(f"columns match expected 40: {lightgbm.columns.tolist()[1:-1] == LIGHTGBM_FEATURE_COLUMNS}")
    print(f"first row: {lightgbm.iloc[0].to_dict()}")
    print(f"last row: {lightgbm.iloc[-1].to_dict()}")
    nan_counts = lightgbm.isna().sum()
    print(f"NaN columns: {nan_counts[nan_counts > 0].to_dict()}")

    print("\nN-BEATS:")
    print(f"y shape: {nbeats['y'].shape}")
    print(f"dates shape: {nbeats['dates'].shape}")
    print(f"first y/date: {float(nbeats['y'][0])}, {nbeats['dates'][0]}")
    print(f"last y/date: {float(nbeats['y'][-1])}, {nbeats['dates'][-1]}")
    print(f"keys: {list(nbeats.keys())}")

    print("\nDiversity check:")
    print("Prophet = minimal inputs")
    print("LightGBM = 40 engineered features")
    print("N-BEATS = 0 engineered features")


if __name__ == "__main__":
    main()
