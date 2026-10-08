import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.wealth_optimization import simulate_wealth_scenarios


@pytest.fixture
def sample_features():
    return pd.DataFrame([
        {
            "user_id": 1,
            "month": "2025-01",
            "monthly_income": 6000.0,
            "monthly_expenses": 4500.0,
            "discretionary_spending": 1200.0,
            "recurring_spending": 2000.0,
        },
        {
            "user_id": 1,
            "month": "2025-02",
            "monthly_income": 6000.0,
            "monthly_expenses": 4500.0,
            "discretionary_spending": 1200.0,
            "recurring_spending": 2000.0,
        },
    ])


def test_wealth_optimization_scenarios(sample_features):
    result = simulate_wealth_scenarios(sample_features, user_id=1)

    assert "baseline_scenario" in result
    assert "alternative_scenarios" in result
    assert len(result["alternative_scenarios"]) == 4

    baseline = result["baseline_scenario"]
    assert baseline["monthly_income"] == 6000.0
    assert baseline["monthly_expenses"] == 4500.0
    assert baseline["monthly_surplus"] == 1500.0
    assert baseline["savings_rate"] == 25.0
    assert "12_months" in baseline["projected_accumulated_savings"]
    assert baseline["projected_accumulated_savings"]["12_months"] == 18000.0

    # Best scenario should have higher surplus than baseline
    assert result["monthly_extra_cash_flow"] > 0
    assert "projected_savings_difference" in result
    assert result["projected_savings_difference"]["12_months"] > 0

    assert len(result["assumptions"]) > 0
    assert len(result["limitations"]) > 0


def test_wealth_optimization_empty_data():
    empty_df = pd.DataFrame()
    res = simulate_wealth_scenarios(empty_df, user_id=1)
    assert "error" in res
