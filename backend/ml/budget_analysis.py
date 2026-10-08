from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np


def generate_sample_budgets(
    transactions_df: pd.DataFrame,
    user_id: Optional[int] = None,
    buffer_pct: float = 1.05,
) -> pd.DataFrame:
    """
    Generate realistic benchmark category budgets for each active month of a user
    derived from actual historical spending patterns.
    """
    if transactions_df.empty:
        return pd.DataFrame(columns=["user_id", "category", "month", "budget_amount"])

    df = transactions_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    expense_df = df[df["transaction_type"] == "expense"]

    if expense_df.empty:
        return pd.DataFrame(columns=["user_id", "category", "month", "budget_amount"])

    # Baseline monthly average by user and category
    avg_cat_spend = (
        expense_df.groupby(["user_id", "category"])["amount"]
        .mean()
        .reset_index()
    )

    all_months = sorted(df["month"].unique())
    users = sorted(df["user_id"].unique())

    budget_rows = []
    for uid in users:
        user_cats = avg_cat_spend[avg_cat_spend["user_id"] == uid]
        for m in all_months:
            for _, row in user_cats.iterrows():
                # Provide a realistic budget target (e.g. rounded baseline)
                base_amt = float(row["amount"])
                budget_amt = round(max(50.0, round(base_amt * buffer_pct, -1)), 2)
                budget_rows.append({
                    "user_id": int(uid),
                    "category": str(row["category"]),
                    "month": m,
                    "budget_amount": budget_amt,
                })

    budgets_df = pd.DataFrame(budget_rows)
    return budgets_df


def track_budgets(
    transactions_df: pd.DataFrame,
    budgets_df: pd.DataFrame,
    month: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Evaluate actual spending against allocated budgets.
    
    Calculates:
    - budget amount
    - actual spending
    - variance (actual - budget)
    - variance percentage
    - remaining budget (budget - actual)
    - overspending status
    """
    if budgets_df.empty:
        return {
            "month": month,
            "user_id": user_id,
            "total_budget": 0.0,
            "total_actual": 0.0,
            "total_variance": 0.0,
            "overall_is_overspending": False,
            "overall_status": "no_budget_data",
            "categories": [],
        }

    b_df = budgets_df.copy()
    t_df = transactions_df.copy()

    if user_id is not None:
        b_df = b_df[b_df["user_id"] == user_id]
        t_df = t_df[t_df["user_id"] == user_id]

    if not t_df.empty:
        t_df["date"] = pd.to_datetime(t_df["date"])
        t_df["month"] = t_df["date"].dt.strftime("%Y-%m")

    # Filter by specific month or choose most recent
    target_month = month
    if target_month is None:
        if not b_df.empty and "month" in b_df.columns:
            target_month = sorted(b_df["month"].unique())[-1]
        elif not t_df.empty and "month" in t_df.columns:
            target_month = sorted(t_df["month"].unique())[-1]

    if target_month:
        b_df = b_df[b_df["month"] == target_month]
        if not t_df.empty:
            t_df = t_df[t_df["month"] == target_month]

    # Calculate actual spending per category for this month
    expense_txs = t_df[t_df["transaction_type"] == "expense"] if not t_df.empty else pd.DataFrame()
    actual_spending_map = (
        expense_txs.groupby("category")["amount"].sum().to_dict()
        if not expense_txs.empty
        else {}
    )

    category_results: List[Dict[str, Any]] = []
    total_budget = 0.0
    total_actual = 0.0

    # Process all budgeted categories
    seen_categories = set()
    for _, brow in b_df.iterrows():
        cat = str(brow["category"])
        seen_categories.add(cat)
        budget_amt = round(float(brow["budget_amount"]), 2)
        actual_amt = round(float(actual_spending_map.get(cat, 0.0)), 2)

        variance = round(actual_amt - budget_amt, 2)
        variance_pct = round((variance / budget_amt) * 100.0, 2) if budget_amt > 0 else 0.0
        remaining = round(budget_amt - actual_amt, 2)
        is_over = actual_amt > budget_amt

        if is_over:
            status = "over_budget"
        elif actual_amt >= 0.85 * budget_amt:
            status = "warning"
        else:
            status = "within_budget"

        total_budget += budget_amt
        total_actual += actual_amt

        category_results.append({
            "category": cat,
            "month": target_month or "all",
            "budget_amount": budget_amt,
            "actual_spending": actual_amt,
            "variance": variance,
            "variance_percentage": variance_pct,
            "remaining_budget": remaining,
            "is_overspending": is_over,
            "status": status,
        })

    # Include unbudgeted categories that had spending
    for cat, actual_amt in actual_spending_map.items():
        if cat not in seen_categories:
            actual_amt = round(float(actual_amt), 2)
            total_actual += actual_amt
            category_results.append({
                "category": cat,
                "month": target_month or "all",
                "budget_amount": 0.0,
                "actual_spending": actual_amt,
                "variance": actual_amt,
                "variance_percentage": 100.0,
                "remaining_budget": round(-actual_amt, 2),
                "is_overspending": True,
                "status": "over_budget",
            })

    total_budget = round(total_budget, 2)
    total_actual = round(total_actual, 2)
    total_variance = round(total_actual - total_budget, 2)
    overall_is_over = total_actual > total_budget
    overall_status = "over_budget" if overall_is_over else ("warning" if total_actual >= 0.85 * total_budget else "within_budget")

    return {
        "month": target_month,
        "user_id": user_id,
        "total_budget": total_budget,
        "total_actual": total_actual,
        "total_variance": total_variance,
        "overall_is_overspending": overall_is_over,
        "overall_status": overall_status,
        "categories": category_results,
    }
