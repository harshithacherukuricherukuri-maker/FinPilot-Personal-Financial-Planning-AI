from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


@dataclass
class BehaviorThresholds:
    """Configurable thresholds for behavioral metric evaluation."""
    low_savings_rate_pct: float = 20.0
    negative_savings_rate_pct: float = 0.0
    high_spending_ratio_pct: float = 80.0
    high_recurring_expense_ratio_pct: float = 45.0
    high_category_concentration_pct: float = 40.0
    volatility_cv_threshold: float = 0.30  # Coefficient of variation (std / mean)
    expense_increase_pct: float = 10.0


def analyze_financial_behavior(
    features_df: pd.DataFrame,
    thresholds: Optional[BehaviorThresholds] = None,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Analyze engineered features to produce objective, data-supported behavior indicators.
    
    Returns structured list of indicators:
    [
        {
            "indicator": str,
            "metric": str,
            "value": float,
            "interpretation": str
        }
    ]
    """
    if features_df.empty:
        return []

    cfg = thresholds or BehaviorThresholds()
    df = features_df.copy()

    if user_id is not None:
        df = df[df["user_id"] == user_id]
        if df.empty:
            return []

    # Sort chronologically
    df = df.sort_values(by="month").reset_index(drop=True)
    indicators: List[Dict[str, Any]] = []

    # 1. Savings Rate Analysis (Average over available history)
    avg_income = float(df["monthly_income"].mean())
    avg_expenses = float(df["monthly_expenses"].mean())
    avg_savings_rate = float(df["savings_rate"].mean())

    if avg_savings_rate < cfg.negative_savings_rate_pct:
        indicators.append({
            "indicator": "Negative Savings",
            "metric": "average_savings_rate_pct",
            "value": round(avg_savings_rate, 2),
            "interpretation": f"Average savings rate is negative at {avg_savings_rate:.2f}%, indicating monthly spending exceeds income.",
        })
    elif avg_savings_rate < cfg.low_savings_rate_pct:
        indicators.append({
            "indicator": "Low Savings",
            "metric": "average_savings_rate_pct",
            "value": round(avg_savings_rate, 2),
            "interpretation": f"Average savings rate is {avg_savings_rate:.2f}%, which is below the benchmark of {cfg.low_savings_rate_pct}%.",
        })
    else:
        indicators.append({
            "indicator": "Healthy Savings",
            "metric": "average_savings_rate_pct",
            "value": round(avg_savings_rate, 2),
            "interpretation": f"Average savings rate is robust at {avg_savings_rate:.2f}%, meeting or exceeding the {cfg.low_savings_rate_pct}% benchmark.",
        })

    # 2. Spending-to-Income Ratio Analysis
    spending_ratio = (avg_expenses / avg_income * 100.0) if avg_income > 0 else 100.0
    if spending_ratio >= cfg.high_spending_ratio_pct:
        indicators.append({
            "indicator": "High Spending",
            "metric": "spending_to_income_ratio_pct",
            "value": round(spending_ratio, 2),
            "interpretation": f"Average spending accounts for {spending_ratio:.2f}% of income, exceeding the {cfg.high_spending_ratio_pct}% high-spending threshold.",
        })
    else:
        indicators.append({
            "indicator": "Controlled Spending",
            "metric": "spending_to_income_ratio_pct",
            "value": round(spending_ratio, 2),
            "interpretation": f"Average spending represents {spending_ratio:.2f}% of income, remaining safely below the {cfg.high_spending_ratio_pct}% threshold.",
        })

    # 3. Expense Trend (Month-over-Month Growth in recent months)
    if len(df) >= 2:
        recent_expenses = df["monthly_expenses"].iloc[-1]
        previous_expenses = df["monthly_expenses"].iloc[-2]
        if previous_expenses > 0:
            growth_pct = ((recent_expenses - previous_expenses) / previous_expenses) * 100.0
            if growth_pct >= cfg.expense_increase_pct:
                indicators.append({
                    "indicator": "Increasing Expenses",
                    "metric": "mom_expense_growth_pct",
                    "value": round(growth_pct, 2),
                    "interpretation": f"Monthly expenses grew by {growth_pct:.2f}% compared to the previous month, surpassing the {cfg.expense_increase_pct}% change threshold.",
                })
            elif growth_pct <= -cfg.expense_increase_pct:
                indicators.append({
                    "indicator": "Decreasing Expenses",
                    "metric": "mom_expense_growth_pct",
                    "value": round(growth_pct, 2),
                    "interpretation": f"Monthly expenses decreased by {abs(growth_pct):.2f}% compared to the previous month.",
                })
            else:
                indicators.append({
                    "indicator": "Stable Spending Trend",
                    "metric": "mom_expense_growth_pct",
                    "value": round(growth_pct, 2),
                    "interpretation": f"Monthly expense change of {growth_pct:.2f}% indicates stable month-over-month expenditure.",
                })

    # 4. Recurring Expense Proportion
    if "recurring_spending" in df.columns and avg_expenses > 0:
        avg_recurring = float(df["recurring_spending"].mean())
        recurring_ratio = (avg_recurring / avg_expenses) * 100.0
        if recurring_ratio >= cfg.high_recurring_expense_ratio_pct:
            indicators.append({
                "indicator": "High Recurring Expenses",
                "metric": "recurring_to_expense_ratio_pct",
                "value": round(recurring_ratio, 2),
                "interpretation": f"Fixed and recurring commitments make up {recurring_ratio:.2f}% of monthly expenditure, exceeding the {cfg.high_recurring_expense_ratio_pct}% threshold.",
            })
        else:
            indicators.append({
                "indicator": "Moderate Recurring Expenses",
                "metric": "recurring_to_expense_ratio_pct",
                "value": round(recurring_ratio, 2),
                "interpretation": f"Recurring commitments account for {recurring_ratio:.2f}% of expenses, within manageable levels.",
            })

    # 5. Category Concentration
    if "category_concentration" in df.columns:
        avg_concentration = float(df["category_concentration"].mean())
        top_cats = df["top_category"].mode()
        primary_cat = top_cats.iloc[0] if not top_cats.empty else "Primary"
        if avg_concentration >= cfg.high_category_concentration_pct:
            indicators.append({
                "indicator": "High Category Concentration",
                "metric": "top_category_concentration_pct",
                "value": round(avg_concentration, 2),
                "interpretation": f"Spending is heavily concentrated in {primary_cat}, representing an average of {avg_concentration:.2f}% of total monthly expenses.",
            })
        else:
            indicators.append({
                "indicator": "Balanced Category Spending",
                "metric": "top_category_concentration_pct",
                "value": round(avg_concentration, 2),
                "interpretation": f"Top category ({primary_cat}) accounts for {avg_concentration:.2f}% of expenses, showing diversified spending across categories.",
            })

    # 6. Spending Volatility Across Months (Coefficient of Variation)
    if len(df) >= 3 and avg_expenses > 0:
        expense_std = float(df["monthly_expenses"].std())
        cv = expense_std / avg_expenses
        if cv >= cfg.volatility_cv_threshold:
            indicators.append({
                "indicator": "Unstable Spending",
                "metric": "monthly_spending_cv",
                "value": round(cv, 3),
                "interpretation": f"Coefficient of variation in monthly expenditure is {cv:.3f}, indicating irregular or volatile spending patterns across months.",
            })
        else:
            indicators.append({
                "indicator": "Stable Spending",
                "metric": "monthly_spending_cv",
                "value": round(cv, 3),
                "interpretation": f"Expenditure coefficient of variation is {cv:.3f}, indicating consistent and predictable month-to-month spending.",
            })

    return indicators
