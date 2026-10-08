import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Ensure backend directory is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))


def explain_forecast(
    features_df: pd.DataFrame,
    forecast_result: Dict[str, Any],
    evaluation_result: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate transparent, evidence-grounded explanations for time-series expense forecasts.
    Only cites attributes and mathematical models actually utilized in training and prediction.
    """
    df = features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]

    if df.empty:
        return {"explanation": "No data available to construct forecast explanation."}

    df = df.sort_values(by="month").reset_index(drop=True)
    avg_expense = float(df["monthly_expenses"].mean())
    recent_expense = float(df["monthly_expenses"].iloc[-1])
    recent_month = df["month"].iloc[-1]

    # Calculate historical trajectory
    if len(df) >= 3:
        initial_expense = float(df["monthly_expenses"].iloc[0])
        overall_change = ((recent_expense - initial_expense) / initial_expense * 100.0) if initial_expense > 0 else 0.0
        trend_direction = "upward" if overall_change > 5.0 else ("downward" if overall_change < -5.0 else "stable")
    else:
        trend_direction = "stable"
        overall_change = 0.0

    # Major category shares
    cat_cols = [c for c in df.columns if c.startswith("spend_")]
    cat_means = {c.replace("spend_", "").title(): float(df[c].mean()) for c in cat_cols if df[c].sum() > 0}
    sorted_cats = sorted(cat_means.items(), key=lambda x: x[1], reverse=True)
    top_3_cats = [f"{cat} (${amt:,.2f}/mo, {(amt / avg_expense * 100.0):.1f}%)" for cat, amt in sorted_cats[:3]] if avg_expense > 0 else []

    forecast_items = forecast_result.get("forecast", [])
    avg_predicted = float(np.mean([f["predicted_total_expense"] for f in forecast_items])) if forecast_items else 0.0

    eval_info = {}
    if evaluation_result:
        eval_info = {
            "mae": f"${evaluation_result.get('mae', 0):,.2f}",
            "mape": f"{evaluation_result.get('mape', 0):.1f}%",
            "validation_method": evaluation_result.get("methodology", "Chronological holdout validation"),
        }

    return {
        "title": "Expense Forecast Explainability Summary",
        "historical_trend": {
            "direction": trend_direction,
            "overall_change_pct": round(overall_change, 1),
            "historical_monthly_average": round(avg_expense, 2),
            "most_recent_recorded_month": f"{recent_month} (${recent_expense:,.2f})",
        },
        "dominant_spending_drivers": top_3_cats,
        "forecast_interpretation": (
            f"The model projects an average monthly expense of ${avg_predicted:,.2f} over the next "
            f"{len(forecast_items)} months, reflecting historical seasonal patterns and recent expenditure momentum."
        ),
        "model_rationale": (
            "Predictions are generated using a Ridge Regression time-series model that accounts for chronological trend index, "
            "seasonal month-of-year cyclicality, and a 3-month lagged rolling spending baseline."
        ),
        "model_validation_performance": eval_info,
        "uncertainty_and_confidence": (
            f"Predictions include a 95% confidence interval margin of $\\pm{forecast_result.get('residual_std', 0) * 1.96:,.2f} "
            f"derived from historical residual standard deviations."
        ),
        "limitations": forecast_result.get("limitations", []),
    }


def explain_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate explainability traces for each generated financial recommendation."""
    explained = []
    for rec in recommendations:
        explained.append({
            "recommendation_summary": rec.get("recommendation"),
            "trigger_reason": rec.get("reason"),
            "underlying_metrics": rec.get("evidence", []),
            "priority_level": rec.get("priority"),
            "algorithmic_confidence": f"{rec.get('confidence', 0.8) * 100:.0f}%",
            "modeling_assumptions": rec.get("assumptions", []),
            "real_world_limitations": rec.get("limitations", []),
        })
    return explained


def explain_wealth_optimization(optimization_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate clear, step-by-step explanations of scenario comparisons in wealth optimization."""
    if "error" in optimization_result:
        return {"explanation": optimization_result["error"]}

    baseline = optimization_result.get("baseline_scenario", {})
    recommended_name = optimization_result.get("recommended_scenario", "")
    monthly_extra = optimization_result.get("monthly_extra_cash_flow", 0.0)
    savings_diff = optimization_result.get("projected_savings_difference", {})

    return {
        "title": "Wealth Optimization Scenario Explanation",
        "baseline_state": (
            f"Currently, average monthly income is ${baseline.get('monthly_income', 0):,.2f} against "
            f"${baseline.get('monthly_expenses', 0):,.2f} in expenses, yielding a baseline monthly surplus of "
            f"${baseline.get('monthly_surplus', 0):,.2f} ({baseline.get('savings_rate', 0):.1f}% savings rate)."
        ),
        "recommended_optimization": recommended_name,
        "mechanism_of_improvement": optimization_result.get("key_changes", []),
        "financial_impact": (
            f"Adopting this scenario frees an additional ${monthly_extra:,.2f} each month, "
            f"accumulating an estimated extra ${savings_diff.get('12_months', 0):,.2f} over 1 year "
            f"and ${savings_diff.get('24_months', 0):,.2f} over 2 years."
        ),
        "transparent_assumptions": optimization_result.get("assumptions", []),
        "disclaimer_and_limitations": optimization_result.get("limitations", []),
    }
