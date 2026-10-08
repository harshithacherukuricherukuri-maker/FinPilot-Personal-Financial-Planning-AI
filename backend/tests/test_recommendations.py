import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.recommendation import (
    generate_budget_recommendations,
    generate_investment_decision_support,
)


def create_profile_df(discretionary_amt: float, savings_rate: float, net_flow: float):
    return pd.DataFrame([
        {
            "user_id": 1,
            "month": "2025-01",
            "monthly_income": 5000.0,
            "monthly_expenses": 5000.0 - net_flow,
            "monthly_net_cash_flow": net_flow,
            "savings_rate": savings_rate,
            "discretionary_spending": discretionary_amt,
            "recurring_spending": 1800.0,
            "category_concentration": 30.0,
            "top_category": "Food",
        },
        {
            "user_id": 1,
            "month": "2025-02",
            "monthly_income": 5000.0,
            "monthly_expenses": 5000.0 - net_flow,
            "monthly_net_cash_flow": net_flow,
            "savings_rate": savings_rate,
            "discretionary_spending": discretionary_amt,
            "recurring_spending": 1800.0,
            "category_concentration": 30.0,
            "top_category": "Food",
        },
    ])


def test_recommendations_change_with_data_changes():
    # Profile A: High discretionary ($2000 of $4000 expenses = 50%), healthy savings rate 20%
    profile_a = create_profile_df(discretionary_amt=2000.0, savings_rate=20.0, net_flow=1000.0)
    recs_a = generate_budget_recommendations(profile_a, user_id=1)
    recs_a_text = [r["recommendation"] for r in recs_a]

    assert any("discretionary" in r.lower() for r in recs_a_text)

    # Profile B: Low discretionary ($300), low savings rate (5%)
    profile_b = create_profile_df(discretionary_amt=300.0, savings_rate=5.0, net_flow=250.0)
    recs_b = generate_budget_recommendations(profile_b, user_id=1)
    recs_b_text = [r["recommendation"] for r in recs_b]

    # Must change dynamically
    assert not any("discretionary" in r.lower() for r in recs_b_text)
    assert any("savings rate" in r.lower() for r in recs_b_text)


def test_recommendation_structure_integrity():
    profile = create_profile_df(discretionary_amt=1800.0, savings_rate=10.0, net_flow=500.0)
    recs = generate_budget_recommendations(profile, user_id=1)

    required_fields = {
        "recommendation", "reason", "evidence", "priority",
        "confidence", "assumptions", "limitations",
    }
    for r in recs:
        assert required_fields.issubset(r.keys())
        assert isinstance(r["evidence"], list) and len(r["evidence"]) > 0
        assert isinstance(r["assumptions"], list) and len(r["assumptions"]) > 0
        assert isinstance(r["limitations"], list) and len(r["limitations"]) > 0
        assert 0.0 <= r["confidence"] <= 1.0


def test_investment_decision_support_insufficient_data_on_negative_cash_flow():
    deficit_df = create_profile_df(discretionary_amt=1000.0, savings_rate=-10.0, net_flow=-500.0)
    result = generate_investment_decision_support(deficit_df, user_id=1)

    assert result["status"] == "insufficient_data"
    assert "Insufficient financial information" in result["message"]
    # Recommends cash flow stabilization first
    assert any("stabilization" in rec["guidance"].lower() for rec in result["recommendations"])


def test_investment_decision_support_with_planning_inputs():
    surplus_df = create_profile_df(discretionary_amt=600.0, savings_rate=30.0, net_flow=1500.0)
    planning = {"risk_tolerance": "aggressive", "has_emergency_fund": True}

    result = generate_investment_decision_support(surplus_df, user_id=1, user_planning_input=planning)

    assert result["status"] == "ready"
    assert result["risk_profile_evaluated"] == "aggressive"
    assert result["monthly_investable_surplus"] == 1500.0
    assert "disclaimer" in result
