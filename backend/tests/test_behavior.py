import sys
from pathlib import Path
import pytest
import pandas as pd

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.behavior_analysis import (
    analyze_financial_behavior,
    BehaviorThresholds,
)


def sample_feature_df():
    return pd.DataFrame([
        {
            "user_id": 1,
            "month": "2025-01",
            "monthly_income": 5000.0,
            "monthly_expenses": 4200.0,  # 84% spending ratio
            "monthly_net_cash_flow": 800.0,
            "savings_rate": 16.0,  # Below 20%
            "recurring_spending": 2200.0,  # >50% recurring
            "category_concentration": 45.0,  # >40%
            "top_category": "Housing",
        },
        {
            "user_id": 1,
            "month": "2025-02",
            "monthly_income": 5000.0,
            "monthly_expenses": 4800.0,  # +14.2% growth (Increasing expenses)
            "monthly_net_cash_flow": 200.0,
            "savings_rate": 4.0,
            "recurring_spending": 2200.0,
            "category_concentration": 42.0,
            "top_category": "Housing",
        },
    ])


def test_behavior_output_structure():
    df = sample_feature_df()
    indicators = analyze_financial_behavior(df, user_id=1)

    assert len(indicators) > 0
    required_keys = {"indicator", "metric", "value", "interpretation"}
    for ind in indicators:
        assert required_keys.issubset(ind.keys())
        assert isinstance(ind["indicator"], str)
        assert isinstance(ind["metric"], str)
        assert isinstance(ind["value"], (int, float))
        assert isinstance(ind["interpretation"], str)
        assert len(ind["interpretation"]) > 0


def test_low_savings_indicator_detection():
    df = sample_feature_df()
    indicators = analyze_financial_behavior(df, user_id=1)
    savings_ind = next((i for i in indicators if i["metric"] == "average_savings_rate_pct"), None)
    assert savings_ind is not None
    assert savings_ind["indicator"] == "Low Savings"
    assert savings_ind["value"] == 10.0  # Average of 16% and 4%


def test_high_spending_indicator_detection():
    df = sample_feature_df()
    indicators = analyze_financial_behavior(df, user_id=1)
    spending_ind = next((i for i in indicators if i["metric"] == "spending_to_income_ratio_pct"), None)
    assert spending_ind is not None
    assert spending_ind["indicator"] == "High Spending"


def test_increasing_expenses_detection():
    df = sample_feature_df()
    indicators = analyze_financial_behavior(df, user_id=1)
    growth_ind = next((i for i in indicators if i["metric"] == "mom_expense_growth_pct"), None)
    assert growth_ind is not None
    assert growth_ind["indicator"] == "Increasing Expenses"
    assert growth_ind["value"] > 10.0


def test_configurable_thresholds():
    df = sample_feature_df()
    # By relaxing the low savings threshold to 5%, average savings of 10% should be considered Healthy Savings
    custom_thresholds = BehaviorThresholds(low_savings_rate_pct=5.0)
    indicators = analyze_financial_behavior(df, thresholds=custom_thresholds, user_id=1)
    savings_ind = next(i for i in indicators if i["metric"] == "average_savings_rate_pct")
    assert savings_ind["indicator"] == "Healthy Savings"


def test_empty_features():
    empty_df = pd.DataFrame()
    indicators = analyze_financial_behavior(empty_df)
    assert indicators == []
