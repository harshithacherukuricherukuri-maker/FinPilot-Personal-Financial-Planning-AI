import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import Ridge

# Ensure backend directory is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

DEFAULT_MODEL_PATH = Path("models/expense_forecast_model.pkl")


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract chronological time-based features from monthly records."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values(by="date").reset_index(drop=True)

    # Chronological time trend index
    start_date = df["date"].iloc[0]
    df["time_idx"] = ((df["date"].dt.year - start_date.year) * 12 + (df["date"].dt.month - start_date.month)).astype(float)

    # Cyclical seasonal features (month of year)
    month_num = df["date"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * month_num / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * month_num / 12.0)

    # 3-month rolling average of historical expenses (lagged to avoid future leakage)
    df["rolling_mean_3m"] = df["monthly_expenses"].shift(1).rolling(window=3, min_periods=1).mean()
    df["rolling_mean_3m"] = df["rolling_mean_3m"].bfill()

    return df


# Ensure unpickler can locate this module regardless of import style
import sys
_current_mod = sys.modules.get(__name__)
if _current_mod:
    sys.modules.setdefault("ml.forecasting", _current_mod)
    sys.modules.setdefault("backend.ml.forecasting", _current_mod)


class ExpenseForecaster:
    """
    Chronological time-series forecasting model for monthly personal expenses.
    Uses trend-regularized Ridge Regression with seasonal components and category decompositions.
    """
    __module__ = "ml.forecasting"

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.total_model = Ridge(alpha=self.alpha)
        self.category_models: Dict[str, Ridge] = {}
        self.feature_cols = ["time_idx", "sin_month", "cos_month", "rolling_mean_3m"]
        self.residual_std: float = 0.0
        self.category_cols: List[str] = []
        self.last_historical_month: Optional[str] = None
        self.last_historical_time_idx: float = 0.0
        self.last_rolling_expense: float = 0.0
        self.is_trained: bool = False

    def fit(self, df: pd.DataFrame) -> "ExpenseForecaster":
        """Fit model strictly on historical monthly feature data in chronological sequence."""
        if len(df) < 4:
            raise ValueError("At least 4 months of historical financial data are required for forecasting.")

        df_feat = add_time_features(df)
        X = df_feat[self.feature_cols]
        y_total = df_feat["monthly_expenses"]

        self.total_model.fit(X, y_total)
        preds = self.total_model.predict(X)
        residuals = y_total - preds
        self.residual_std = float(np.std(residuals)) if len(residuals) > 1 else 100.0

        # Identify category spending columns
        self.category_cols = [c for c in df_feat.columns if c.startswith("spend_")]
        self.category_models = {}
        for cat_col in self.category_cols:
            if df_feat[cat_col].sum() > 0:
                cat_model = Ridge(alpha=self.alpha)
                cat_model.fit(X, df_feat[cat_col])
                self.category_models[cat_col] = cat_model

        self.last_historical_month = df_feat["month"].iloc[-1]
        self.last_historical_time_idx = df_feat["time_idx"].iloc[-1]
        self.last_rolling_expense = float(df_feat["monthly_expenses"].tail(3).mean())
        self.is_trained = True
        return self

    def predict_next_months(self, horizon: int = 3) -> List[Dict[str, Any]]:
        """Forecast the next horizon months into the future with category breakdowns and prediction bounds."""
        if not self.is_trained:
            raise RuntimeError("Forecasting model has not been trained yet.")

        forecasts = []
        last_dt = pd.to_datetime(self.last_historical_month + "-01")
        current_rolling = self.last_rolling_expense

        for step in range(1, horizon + 1):
            future_dt = last_dt + pd.DateOffset(months=step)
            future_month = future_dt.strftime("%Y-%m")
            future_time_idx = self.last_historical_time_idx + step
            month_num = future_dt.month

            X_future = pd.DataFrame([{
                "time_idx": future_time_idx,
                "sin_month": np.sin(2 * np.pi * month_num / 12.0),
                "cos_month": np.cos(2 * np.pi * month_num / 12.0),
                "rolling_mean_3m": current_rolling,
            }])

            pred_total = float(self.total_model.predict(X_future)[0])
            pred_total = round(max(0.0, pred_total), 2)

            # 95% Confidence Interval based on training residuals
            ci_margin = round(1.96 * self.residual_std, 2)
            lower_ci = round(max(0.0, pred_total - ci_margin), 2)
            upper_ci = round(pred_total + ci_margin, 2)

            # Predict individual categories
            cat_breakdown: Dict[str, float] = {}
            for cat_col, model in self.category_models.items():
                cat_name = cat_col.replace("spend_", "").title()
                cat_pred = float(model.predict(X_future)[0])
                cat_breakdown[cat_name] = round(max(0.0, cat_pred), 2)

            forecasts.append({
                "month": future_month,
                "step": step,
                "predicted_total_expense": pred_total,
                "confidence_lower": lower_ci,
                "confidence_upper": upper_ci,
                "confidence_margin": ci_margin,
                "category_forecasts": cat_breakdown,
            })

            # Update rolling mean autoregressively
            current_rolling = (current_rolling * 2 + pred_total) / 3.0

        return forecasts


def train_and_save_forecast_model(
    monthly_features_df: pd.DataFrame,
    user_id: Optional[int] = 1,
    output_path: Path = DEFAULT_MODEL_PATH,
) -> ExpenseForecaster:
    """Train expense forecaster and save model artifact to disk."""
    df = monthly_features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]

    forecaster = ExpenseForecaster()
    forecaster.fit(df)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(forecaster, output_path)
    return forecaster


def load_forecasting_model(model_path: Path = DEFAULT_MODEL_PATH) -> Optional[ExpenseForecaster]:
    """Load pre-trained forecasting model artifact if present."""
    path = Path(model_path)
    if path.exists():
        return joblib.load(path)
    return None


def forecast_expenses(
    monthly_features_df: pd.DataFrame,
    user_id: Optional[int] = 1,
    horizon: int = 3,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> Dict[str, Any]:
    """
    High-level forecasting interface providing prediction records, model metadata,
    and responsible AI uncertainty bounds.
    """
    df = monthly_features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]

    if len(df) < 4:
        return {
            "forecast": [],
            "model": "Ridge Regression (Time-Series Regularized)",
            "horizon": horizon,
            "status": "insufficient_data",
            "message": "At least 4 months of transaction history are required to construct an expense forecast.",
            "assumptions": [],
            "limitations": ["Insufficient historical time series to calculate trends."],
        }

    # Attempt to load model or train fresh on available history
    forecaster = load_forecasting_model(model_path)
    if forecaster is None or not forecaster.is_trained:
        forecaster = train_and_save_forecast_model(df, user_id=user_id, output_path=model_path)

    predictions = forecaster.predict_next_months(horizon=horizon)

    return {
        "forecast": predictions,
        "model": "Ridge Regression (Time-Series Regularized with Seasonality)",
        "horizon": horizon,
        "historical_period": f"{df['month'].iloc[0]} to {df['month'].iloc[-1]}",
        "historical_months_count": len(df),
        "residual_std": round(forecaster.residual_std, 2),
        "assumptions": [
            "Assumes spending patterns follow historical trend and seasonal baseline.",
            "Assumes no major macroeconomic anomalies or unobserved one-time life events.",
            "Category decomposition reflects recurring commitments and historical category shares.",
        ],
        "limitations": [
            "Forecast precision declines beyond 3-6 months.",
            "Unanticipated emergency expenses cannot be predicted from ordinary recurring trends.",
            "Educational decision-support forecast only; not a financial guarantee.",
        ],
    }
