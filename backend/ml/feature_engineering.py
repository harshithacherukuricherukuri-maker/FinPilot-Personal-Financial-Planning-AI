import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

ESSENTIAL_CATEGORIES = {"Housing", "Utilities", "Food", "Healthcare", "Transport"}
DISCRETIONARY_CATEGORIES = {"Shopping", "Entertainment", "Subscription", "Other"}
RECURRING_CATEGORIES = {"Housing", "Utilities", "Subscription"}


def calculate_monthly_features(
    df: pd.DataFrame,
    user_id: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate comprehensive monthly financial features from processed transactions.
    
    Calculates:
    - monthly income
    - monthly expenses
    - monthly net cash flow
    - savings rate ((Net Cash Flow / Income) * 100)
    - category-wise monthly spending
    - transaction frequency
    - average transaction amount
    - spending volatility (std of daily spending)
    - recurring spending
    - essential spending
    - discretionary spending
    - category concentration (max category share & HHI)
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "user_id", "month", "monthly_income", "monthly_expenses", "monthly_net_cash_flow",
            "savings_rate", "transaction_frequency", "average_transaction_amount",
            "spending_volatility", "recurring_spending", "essential_spending",
            "discretionary_spending", "category_concentration", "top_category",
        ])

    df = df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]
        if df.empty:
            return pd.DataFrame()

    # Ensure date is datetime and extract month YYYY-MM
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    df["day"] = df["date"].dt.strftime("%Y-%m-%d")

    records = []
    grouped = df.groupby(["user_id", "month"])

    for (uid, month_str), group in grouped:
        income_txs = group[group["transaction_type"] == "income"]
        expense_txs = group[group["transaction_type"] == "expense"]

        monthly_income = float(income_txs["amount"].sum()) if not income_txs.empty else 0.0
        monthly_expenses = float(expense_txs["amount"].sum()) if not expense_txs.empty else 0.0
        monthly_net_cash_flow = round(monthly_income - monthly_expenses, 2)

        # Savings Rate = (Net Cash Flow / Income) * 100
        if monthly_income > 0:
            savings_rate = round((monthly_net_cash_flow / monthly_income) * 100.0, 2)
        else:
            savings_rate = 0.0

        # Frequency & Averages
        total_frequency = len(group)
        expense_frequency = len(expense_txs)
        avg_tx_amount = round(float(expense_txs["amount"].mean()), 2) if not expense_txs.empty else 0.0

        # Spending volatility: standard deviation of daily expense totals
        if not expense_txs.empty:
            daily_spending = expense_txs.groupby("day")["amount"].sum()
            spending_volatility = round(float(daily_spending.std()), 2) if len(daily_spending) > 1 else 0.0
            if np.isnan(spending_volatility):
                spending_volatility = 0.0
        else:
            spending_volatility = 0.0

        # Category sums
        cat_spending = expense_txs.groupby("category")["amount"].sum().to_dict() if not expense_txs.empty else {}

        # Spending classifications
        recurring_spending = round(sum(
            amount for cat, amount in cat_spending.items() if cat in RECURRING_CATEGORIES
        ), 2)

        essential_spending = round(sum(
            amount for cat, amount in cat_spending.items() if cat in ESSENTIAL_CATEGORIES
        ), 2)

        discretionary_spending = round(sum(
            amount for cat, amount in cat_spending.items() if cat in DISCRETIONARY_CATEGORIES
        ), 2)

        # Category concentration (HHI & top category share)
        if monthly_expenses > 0 and cat_spending:
            sorted_cats = sorted(cat_spending.items(), key=lambda x: x[1], reverse=True)
            top_category = sorted_cats[0][0]
            top_share = sorted_cats[0][1] / monthly_expenses
            # Category concentration as top category share percentage (0 to 100)
            category_concentration = round(top_share * 100.0, 2)
        else:
            top_category = "None"
            category_concentration = 0.0

        record = {
            "user_id": uid,
            "month": month_str,
            "monthly_income": round(monthly_income, 2),
            "monthly_expenses": round(monthly_expenses, 2),
            "monthly_net_cash_flow": monthly_net_cash_flow,
            "savings_rate": savings_rate,
            "transaction_frequency": total_frequency,
            "expense_transaction_count": expense_frequency,
            "average_transaction_amount": avg_tx_amount,
            "spending_volatility": spending_volatility,
            "recurring_spending": recurring_spending,
            "essential_spending": essential_spending,
            "discretionary_spending": discretionary_spending,
            "category_concentration": category_concentration,
            "top_category": top_category,
        }

        # Include individual category expenditures
        for cat, amt in cat_spending.items():
            record[f"spend_{cat.lower()}"] = round(float(amt), 2)

        records.append(record)

    features_df = pd.DataFrame(records)
    if not features_df.empty:
        features_df = features_df.sort_values(by=["user_id", "month"]).reset_index(drop=True)
        features_df = features_df.fillna(0.0)

    return features_df


def calculate_category_spending(
    df: pd.DataFrame,
    month: Optional[str] = None,
    user_id: Optional[int] = None
) -> pd.DataFrame:
    """Calculate aggregated category-level expense spending."""
    if df.empty:
        return pd.DataFrame(columns=["category", "total_amount", "percentage", "transaction_count"])

    df = df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]

    if month is not None:
        df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
        df = df[df["month"] == month]

    expense_df = df[df["transaction_type"] == "expense"]
    if expense_df.empty:
        return pd.DataFrame(columns=["category", "total_amount", "percentage", "transaction_count"])

    total_expense = expense_df["amount"].sum()
    grouped = expense_df.groupby("category").agg(
        total_amount=("amount", "sum"),
        transaction_count=("amount", "count"),
    ).reset_index()

    grouped["total_amount"] = grouped["total_amount"].round(2)
    grouped["percentage"] = (
        (grouped["total_amount"] / total_expense * 100.0).round(2)
        if total_expense > 0 else 0.0
    )
    return grouped.sort_values(by="total_amount", ascending=False).reset_index(drop=True)


def calculate_overall_summary(
    df: pd.DataFrame,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """Calculate aggregate financial summary metrics across transactions."""
    if df.empty:
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_cash_flow": 0.0,
            "savings_rate": 0.0,
            "transaction_count": 0,
            "user_id": user_id,
        }

    subset = df.copy()
    if user_id is not None:
        subset = subset[subset["user_id"] == user_id]

    income = float(subset[subset["transaction_type"] == "income"]["amount"].sum())
    expenses = float(subset[subset["transaction_type"] == "expense"]["amount"].sum())
    net_flow = round(income - expenses, 2)
    savings_rate = round((net_flow / income) * 100.0, 2) if income > 0 else 0.0

    return {
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "net_cash_flow": net_flow,
        "savings_rate": savings_rate,
        "transaction_count": len(subset),
        "user_id": user_id,
    }


def save_monthly_features(
    features_df: pd.DataFrame,
    output_path: Union[str, Path] = "data/processed/monthly_features.csv"
) -> Path:
    """Save engineered monthly features to CSV."""
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(dest, index=False)
    return dest
