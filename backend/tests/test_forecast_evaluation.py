import sys
import json
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.forecast_evaluation import evaluate_forecasting_model


@pytest.fixture
def sample_history():
    """14 months of history to allow 3-month holdout evaluation."""
    months = [f"2025-{m:02d}" for m in range(1, 13)] + ["2026-01", "2026-02"]
    records = []
    for i, m in enumerate(months):
        records.append({
            "user_id": 1,
            "month": m,
            "monthly_income": 5000.0,
            "monthly_expenses": 3200.0 + (i * 15.0),
            "spend_food": 800.0,
            "spend_housing": 1300.0,
        })
    return pd.DataFrame(records)


def test_forecast_evaluation_metrics(sample_history, tmp_path):
    report_file = tmp_path / "test_evaluation.json"
    result = evaluate_forecasting_model(
        sample_history,
        user_id=1,
        test_months_count=3,
        save_path=report_file,
    )

    assert "mae" in result
    assert "rmse" in result
    assert "mape" in result
    assert result["mae"] >= 0.0
    assert result["rmse"] >= 0.0
    assert result["mape"] >= 0.0

    assert result["training_months_count"] == 11
    assert result["evaluation_months_count"] == 3
    assert len(result["comparisons"]) == 3

    # Verify JSON file generation
    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        loaded_json = json.load(f)
    assert loaded_json["mae"] == result["mae"]


def test_evaluation_insufficient_history():
    short_df = pd.DataFrame([
        {"user_id": 1, "month": "2025-01", "monthly_expenses": 3000.0},
        {"user_id": 1, "month": "2025-02", "monthly_expenses": 3100.0},
    ])
    result = evaluate_forecasting_model(short_df, user_id=1, test_months_count=3, save_path=None)
    assert "error" in result
