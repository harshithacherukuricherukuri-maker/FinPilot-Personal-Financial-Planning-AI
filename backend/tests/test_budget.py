import sys
from pathlib import Path
import pytest
import pandas as pd

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.budget_analysis import track_budgets, generate_sample_budgets


def sample_transactions_for_budget():
    return pd.DataFrame([
        # Food: Total spent 550 (Budget 500 -> Over budget)
        {"transaction_id": "T1", "user_id": 1, "date": "2025-01-05", "description": "Grocery", "amount": 350.0, "transaction_type": "expense", "category": "Food"},
        {"transaction_id": "T2", "user_id": 1, "date": "2025-01-12", "description": "Restaurant", "amount": 200.0, "transaction_type": "expense", "category": "Food"},

        # Housing: Total spent 1200 (Budget 1300 -> Within budget)
        {"transaction_id": "T3", "user_id": 1, "date": "2025-01-02", "description": "Rent", "amount": 1200.0, "transaction_type": "expense", "category": "Housing"},

        # Entertainment: Total spent 180 (Budget 200 -> Warning: 90% spent)
        {"transaction_id": "T4", "user_id": 1, "date": "2025-01-18", "description": "Concert", "amount": 180.0, "transaction_type": "expense", "category": "Entertainment"},
    ])


def sample_budgets():
    return pd.DataFrame([
        {"user_id": 1, "category": "Food", "month": "2025-01", "budget_amount": 500.0},
        {"user_id": 1, "category": "Housing", "month": "2025-01", "budget_amount": 1500.0},
        {"user_id": 1, "category": "Entertainment", "month": "2025-01", "budget_amount": 200.0},
    ])


def test_budget_variance_and_overspending():
    tx_df = sample_transactions_for_budget()
    b_df = sample_budgets()

    result = track_budgets(tx_df, b_df, month="2025-01", user_id=1)

    assert result["month"] == "2025-01"
    # Total budget = 500 + 1500 + 200 = 2200
    assert result["total_budget"] == 2200.0
    # Total actual = 550 + 1200 + 180 = 1930
    assert result["total_actual"] == 1930.0
    # Total variance = 1930 - 2200 = -270
    assert result["total_variance"] == -270.0
    assert result["overall_is_overspending"] is False

    cats = {c["category"]: c for c in result["categories"]}

    # Food: spent 550, budget 500 => variance +50, remaining -50, overspending True
    food = cats["Food"]
    assert food["actual_spending"] == 550.0
    assert food["variance"] == 50.0
    assert food["variance_percentage"] == 10.0
    assert food["remaining_budget"] == -50.0
    assert food["is_overspending"] is True
    assert food["status"] == "over_budget"

    # Housing: spent 1200, budget 1500 (80% used) => remaining 300, within_budget
    housing = cats["Housing"]
    assert housing["actual_spending"] == 1200.0
    assert housing["variance"] == -300.0
    assert housing["remaining_budget"] == 300.0
    assert housing["is_overspending"] is False
    assert housing["status"] == "within_budget"

    # Entertainment: spent 180, budget 200 => warning (90% utilized)
    ent = cats["Entertainment"]
    assert ent["actual_spending"] == 180.0
    assert ent["is_overspending"] is False
    assert ent["status"] == "warning"


def test_generate_sample_budgets():
    tx_df = sample_transactions_for_budget()
    b_df = generate_sample_budgets(tx_df, user_id=1)

    assert not b_df.empty
    assert set(b_df.columns) == {"user_id", "category", "month", "budget_amount"}
    assert (b_df["budget_amount"] > 0).all()


def test_empty_budget_data():
    empty_tx = pd.DataFrame()
    empty_b = pd.DataFrame()
    res = track_budgets(empty_tx, empty_b)
    assert res["total_budget"] == 0.0
    assert res["total_actual"] == 0.0
    assert res["categories"] == []
