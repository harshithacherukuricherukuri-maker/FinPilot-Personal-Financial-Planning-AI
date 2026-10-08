import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.forecasting import (
    ExpenseForecaster,
    forecast_expenses,
    train_and_save_forecast_model,
    load_forecasting_model,
)


@pytest.fixture
def sample_history():
    """Create a realistic 12-month sequence of financial features for testing."""
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    records = []
    base_expense = 3000.0
    for i, m in enumerate(months):
        records.append({
            "user_id": 1,
            "month": m,
            "monthly_income": 5000.0,
            "monthly_expenses": base_expense + (i * 20.0) + (100.0 if i % 2 == 0 else -100.0),
            "spend_food": 800.0 + (i * 5.0),
            "spend_housing": 1300.0,
            "spend_utilities": 250.0,
        })
    return pd.DataFrame(records)


def test_expense_forecaster_fit_and_predict(sample_history):
    forecaster = ExpenseForecaster()
    forecaster.fit(sample_history)

    assert forecaster.is_trained
    assert forecaster.residual_std >= 0

    predictions = forecaster.predict_next_months(horizon=3)
    assert len(predictions) == 3

    expected_months = ["2026-01", "2026-02", "2026-03"]
    for i, pred in enumerate(predictions):
        assert pred["month"] == expected_months[i]
        assert pred["step"] == i + 1
        assert pred["predicted_total_expense"] > 0
        # Confidence interval bounds
        assert pred["confidence_lower"] <= pred["predicted_total_expense"]
        assert pred["confidence_upper"] >= pred["predicted_total_expense"]
        assert pred["confidence_margin"] >= 0
        # Category breakdown
        assert "Food" in pred["category_forecasts"]
        assert "Housing" in pred["category_forecasts"]


def test_insufficient_history_handling():
    short_df = pd.DataFrame([
        {"user_id": 1, "month": "2025-01", "monthly_expenses": 3000.0},
        {"user_id": 1, "month": "2025-02", "monthly_expenses": 3100.0},
    ])
    result = forecast_expenses(short_df, user_id=1, horizon=3)
    assert result["status"] == "insufficient_data"
    assert len(result["forecast"]) == 0


def test_model_serialization_roundtrip(sample_history, tmp_path):
    model_file = tmp_path / "test_forecast_model.pkl"
    forecaster = train_and_save_forecast_model(sample_history, user_id=1, output_path=model_file)
    assert model_file.exists()

    loaded = load_forecasting_model(model_file)
    assert loaded is not None
    assert loaded.is_trained

    preds_original = forecaster.predict_next_months(horizon=2)
    preds_loaded = loaded.predict_next_months(horizon=2)

    assert preds_original[0]["predicted_total_expense"] == preds_loaded[0]["predicted_total_expense"]
