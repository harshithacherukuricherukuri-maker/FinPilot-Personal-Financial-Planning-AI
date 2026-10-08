import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from ml.forecasting import ExpenseForecaster

DEFAULT_EVALUATION_PATH = Path("models/forecast_evaluation.json")


def evaluate_forecasting_model(
    monthly_features_df: pd.DataFrame,
    user_id: Optional[int] = 1,
    test_months_count: int = 3,
    save_path: Optional[Path] = DEFAULT_EVALUATION_PATH,
) -> Dict[str, Any]:
    """
    Perform rigorous chronological out-of-time validation of the expense forecasting model.
    
    Methodology:
    - Splits the historical time series chronologically into training period (first N - k months)
      and holdout validation period (last k months).
    - Prevents data leakage by training strictly on prior history.
    - Evaluates prediction accuracy against actual recorded expenses using MAE, RMSE, and MAPE.
    """
    df = monthly_features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]

    df = df.sort_values(by="month").reset_index(drop=True)
    n_records = len(df)

    if n_records < (test_months_count + 3):
        return {
            "error": "Insufficient time-series observations for holdout validation.",
            "min_required": test_months_count + 3,
            "actual_records": n_records,
        }

    # Chronological partition
    train_df = df.iloc[:-test_months_count].copy()
    test_df = df.iloc[-test_months_count:].copy()

    training_period = f"{train_df['month'].iloc[0]} to {train_df['month'].iloc[-1]}"
    evaluation_period = f"{test_df['month'].iloc[0]} to {test_df['month'].iloc[-1]}"

    # Train model strictly on training partition
    forecaster = ExpenseForecaster()
    forecaster.fit(train_df)

    # Multi-step out-of-sample prediction
    predictions = forecaster.predict_next_months(horizon=test_months_count)

    actuals = test_df["monthly_expenses"].values
    preds = np.array([p["predicted_total_expense"] for p in predictions])

    # Error metrics
    abs_errors = np.abs(actuals - preds)
    sq_errors = np.square(actuals - preds)
    # Safe MAPE avoiding division by zero
    pct_errors = abs_errors / np.maximum(np.abs(actuals), 1e-4) * 100.0

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(sq_errors)))
    mape = float(np.mean(pct_errors))

    comparison_records = []
    for i, (_, row) in enumerate(test_df.iterrows()):
        comparison_records.append({
            "month": row["month"],
            "actual": float(row["monthly_expenses"]),
            "predicted": float(preds[i]),
            "absolute_error": round(float(abs_errors[i]), 2),
            "percentage_error": round(float(pct_errors[i]), 2),
        })

    evaluation_report = {
        "model": "Ridge Regression (Time-Series Regularized)",
        "methodology": "Chronological holdout validation without lookahead leakage",
        "training_period": training_period,
        "training_months_count": len(train_df),
        "evaluation_period": evaluation_period,
        "evaluation_months_count": len(test_df),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "comparisons": comparison_records,
        "evaluation_timestamp": pd.Timestamp.now().isoformat(),
    }

    if save_path:
        out_file = Path(save_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(evaluation_report, f, indent=2)

    return evaluation_report
