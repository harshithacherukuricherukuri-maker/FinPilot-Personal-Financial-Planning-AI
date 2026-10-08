import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.explainability import (
    explain_forecast,
    explain_recommendations,
    explain_wealth_optimization,
)


def test_forecast_explainability():
    features_df = pd.DataFrame([
        {"user_id": 1, "month": "2025-01", "monthly_expenses": 3000.0, "spend_food": 900.0, "spend_housing": 1200.0},
        {"user_id": 1, "month": "2025-02", "monthly_expenses": 3200.0, "spend_food": 950.0, "spend_housing": 1200.0},
        {"user_id": 1, "month": "2025-03", "monthly_expenses": 3400.0, "spend_food": 1000.0, "spend_housing": 1200.0},
    ])
    mock_forecast = {
        "forecast": [{"month": "2025-04", "predicted_total_expense": 3500.0}],
        "residual_std": 120.0,
        "limitations": ["Limited horizon"],
    }
    explanation = explain_forecast(features_df, mock_forecast, user_id=1)

    assert "historical_trend" in explanation
    assert explanation["historical_trend"]["direction"] == "upward"
    assert "dominant_spending_drivers" in explanation
    assert len(explanation["dominant_spending_drivers"]) > 0
    assert "model_rationale" in explanation
    assert "uncertainty_and_confidence" in explanation


def test_recommendations_explainability():
    mock_recs = [
        {
            "recommendation": "Cut dining out",
            "reason": "Food spending high",
            "evidence": ["Food is 40% of spend"],
            "priority": "high",
            "confidence": 0.85,
            "assumptions": ["Can cook at home"],
            "limitations": ["Time constraint"],
        }
    ]
    explained = explain_recommendations(mock_recs)
    assert len(explained) == 1
    assert explained[0]["algorithmic_confidence"] == "85%"
    assert "Food is 40% of spend" in explained[0]["underlying_metrics"]


def test_wealth_optimization_explainability():
    mock_opt = {
        "baseline_scenario": {"monthly_income": 5000.0, "monthly_expenses": 3500.0, "monthly_surplus": 1500.0, "savings_rate": 30.0},
        "recommended_scenario": "Trim discretionary",
        "monthly_extra_cash_flow": 250.0,
        "projected_savings_difference": {"12_months": 3000.0, "24_months": 6000.0},
        "key_changes": ["Trim dining by 15%"],
        "assumptions": ["Stable income"],
        "limitations": ["No return guarantee"],
    }
    explanation = explain_wealth_optimization(mock_opt)
    assert "baseline_state" in explanation
    assert "financial_impact" in explanation
    assert "$250.00" in explanation["financial_impact"]
