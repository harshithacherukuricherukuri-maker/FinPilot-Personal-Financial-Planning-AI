import sys
from pathlib import Path
import pytest
import pandas as pd

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.feature_engineering import (
    calculate_monthly_features,
    calculate_category_spending,
    calculate_overall_summary,
)


def sample_transactions():
    return pd.DataFrame([
        # Month 1: 2025-01 (Income: 5000, Expenses: 3000)
        {"transaction_id": "T1", "user_id": 1, "date": "2025-01-01", "description": "Salary", "amount": 5000.0, "transaction_type": "income", "category": "Income"},
        {"transaction_id": "T2", "user_id": 1, "date": "2025-01-02", "description": "Rent", "amount": 1200.0, "transaction_type": "expense", "category": "Housing"},
        {"transaction_id": "T3", "user_id": 1, "date": "2025-01-05", "description": "Groceries", "amount": 800.0, "transaction_type": "expense", "category": "Food"},
        {"transaction_id": "T4", "user_id": 1, "date": "2025-01-10", "description": "Electricity", "amount": 200.0, "transaction_type": "expense", "category": "Utilities"},
        {"transaction_id": "T5", "user_id": 1, "date": "2025-01-15", "description": "Shopping", "amount": 800.0, "transaction_type": "expense", "category": "Shopping"},

        # Month 2: 2025-02 (Income: 5000, Expenses: 2500)
        {"transaction_id": "T6", "user_id": 1, "date": "2025-02-01", "description": "Salary", "amount": 5000.0, "transaction_type": "income", "category": "Income"},
        {"transaction_id": "T7", "user_id": 1, "date": "2025-02-02", "description": "Rent", "amount": 1200.0, "transaction_type": "expense", "category": "Housing"},
        {"transaction_id": "T8", "user_id": 1, "date": "2025-02-05", "description": "Groceries", "amount": 700.0, "transaction_type": "expense", "category": "Food"},
        {"transaction_id": "T9", "user_id": 1, "date": "2025-02-12", "description": "Netflix", "amount": 20.0, "transaction_type": "expense", "category": "Subscription"},
        {"transaction_id": "T10", "user_id": 1, "date": "2025-02-20", "description": "Shopping", "amount": 580.0, "transaction_type": "expense", "category": "Shopping"},
    ])


def test_monthly_feature_calculations():
    df = sample_transactions()
    feats = calculate_monthly_features(df, user_id=1)

    assert len(feats) == 2
    m1 = feats[feats["month"] == "2025-01"].iloc[0]
    assert m1["monthly_income"] == 5000.0
    assert m1["monthly_expenses"] == 3000.0
    assert m1["monthly_net_cash_flow"] == 2000.0
    # Savings rate: (2000 / 5000) * 100 = 40.0%
    assert m1["savings_rate"] == 40.0

    # Essential: Housing(1200) + Food(800) + Utilities(200) = 2200
    assert m1["essential_spending"] == 2200.0
    # Discretionary: Shopping(800) = 800
    assert m1["discretionary_spending"] == 800.0
    # Recurring: Housing(1200) + Utilities(200) = 1400
    assert m1["recurring_spending"] == 1400.0


def test_zero_income_savings_rate_safety():
    df = pd.DataFrame([
        {"transaction_id": "T1", "user_id": 1, "date": "2025-03-01", "description": "Groceries", "amount": 500.0, "transaction_type": "expense", "category": "Food"},
    ])
    feats = calculate_monthly_features(df, user_id=1)
    assert len(feats) == 1
    row = feats.iloc[0]
    assert row["monthly_income"] == 0.0
    assert row["monthly_expenses"] == 500.0
    assert row["monthly_net_cash_flow"] == -500.0
    # Should safely be 0.0 without divide-by-zero error or inf
    assert row["savings_rate"] == 0.0


def test_category_spending_calculation():
    df = sample_transactions()
    cat_df = calculate_category_spending(df, month="2025-01", user_id=1)

    assert not cat_df.empty
    assert "Housing" in cat_df["category"].values
    assert "Food" in cat_df["category"].values

    total_expense = cat_df["total_amount"].sum()
    assert total_expense == 3000.0

    housing_row = cat_df[cat_df["category"] == "Housing"].iloc[0]
    assert housing_row["total_amount"] == 1200.0
    # 1200 / 3000 = 40.0%
    assert housing_row["percentage"] == 40.0


def test_overall_summary_calculation():
    df = sample_transactions()
    summary = calculate_overall_summary(df, user_id=1)

    assert summary["total_income"] == 10000.0
    assert summary["total_expenses"] == 5500.0
    assert summary["net_cash_flow"] == 4500.0
    # 4500 / 10000 = 45.0%
    assert summary["savings_rate"] == 45.0
    assert summary["transaction_count"] == 10


def test_empty_dataset_handling():
    empty_df = pd.DataFrame()
    feats = calculate_monthly_features(empty_df)
    assert feats.empty

    cats = calculate_category_spending(empty_df)
    assert cats.empty

    summary = calculate_overall_summary(empty_df)
    assert summary["total_income"] == 0.0
    assert summary["total_expenses"] == 0.0
    assert summary["savings_rate"] == 0.0
