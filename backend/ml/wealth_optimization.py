import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Ensure backend directory is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))


def simulate_wealth_scenarios(
    features_df: pd.DataFrame,
    user_id: Optional[int] = None,
    planning_horizons: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Perform scenario-based wealth optimization using actual historical spending averages.
    
    Evaluates:
    - Baseline: Current average spending pattern
    - Scenario 1: Moderate Discretionary Optimization (15% reduction in discretionary spending)
    - Scenario 2: Aggressive Discretionary Optimization (30% reduction in discretionary spending)
    - Scenario 3: Recurring Commitments Optimization (10% reduction in recurring expenses)
    - Scenario 4: Combined Optimization (15% discretionary + 10% recurring reduction)
    
    Projected savings are computed mathematically across planning horizons.
    Projections are clearly labeled as assumptions-based scenarios with no guaranteed returns.
    """
    if features_df.empty:
        return {"error": "No financial features available for wealth optimization."}

    df = features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]
        if df.empty:
            return {"error": f"No features found for user_id={user_id}."}

    horizons = planning_horizons or [6, 12, 24, 36]

    # Baseline monthly averages derived strictly from real processed data
    avg_income = round(float(df["monthly_income"].mean()), 2)
    avg_expenses = round(float(df["monthly_expenses"].mean()), 2)
    avg_discretionary = round(float(df["discretionary_spending"].mean()), 2) if "discretionary_spending" in df.columns else 0.0
    avg_recurring = round(float(df["recurring_spending"].mean()), 2) if "recurring_spending" in df.columns else 0.0

    # 1. Baseline Scenario
    baseline_surplus = round(max(0.0, avg_income - avg_expenses), 2)
    baseline_savings_rate = round((baseline_surplus / avg_income * 100.0), 2) if avg_income > 0 else 0.0
    baseline_projections = {f"{h}_months": round(baseline_surplus * h, 2) for h in horizons}

    baseline_scenario = {
        "scenario_id": "baseline",
        "name": "Current Spending Pattern (Baseline)",
        "monthly_income": avg_income,
        "monthly_expenses": avg_expenses,
        "monthly_discretionary": avg_discretionary,
        "monthly_recurring": avg_recurring,
        "monthly_surplus": baseline_surplus,
        "savings_rate": baseline_savings_rate,
        "projected_accumulated_savings": baseline_projections,
        "monthly_savings_improvement": 0.0,
    }

    # Helper to build alternative scenario
    def build_scenario(scenario_id: str, name: str, disc_reduction_pct: float, rec_reduction_pct: float) -> Dict[str, Any]:
        disc_saved = round(avg_discretionary * (disc_reduction_pct / 100.0), 2)
        rec_saved = round(avg_recurring * (rec_reduction_pct / 100.0), 2)
        total_monthly_saved = round(disc_saved + rec_saved, 2)

        new_expenses = round(max(0.0, avg_expenses - total_monthly_saved), 2)
        new_surplus = round(max(0.0, avg_income - new_expenses), 2)
        new_savings_rate = round((new_surplus / avg_income * 100.0), 2) if avg_income > 0 else 0.0
        projections = {f"{h}_months": round(new_surplus * h, 2) for h in horizons}

        return {
            "scenario_id": scenario_id,
            "name": name,
            "monthly_income": avg_income,
            "monthly_expenses": new_expenses,
            "monthly_surplus": new_surplus,
            "savings_rate": new_savings_rate,
            "monthly_savings_improvement": total_monthly_saved,
            "projected_accumulated_savings": projections,
            "actions": [
                f"Reduce discretionary outlays by {disc_reduction_pct:.0f}% (saving ${disc_saved:,.2f}/mo)" if disc_reduction_pct > 0 else None,
                f"Renegotiate/trim recurring bills by {rec_reduction_pct:.0f}% (saving ${rec_saved:,.2f}/mo)" if rec_reduction_pct > 0 else None,
            ],
        }

    alternatives = [
        build_scenario("moderate_discretionary", "Moderate Discretionary Optimization (15% trim)", 15.0, 0.0),
        build_scenario("aggressive_discretionary", "Aggressive Discretionary Optimization (30% trim)", 30.0, 0.0),
        build_scenario("recurring_reduction", "Recurring Commitment Trim (10% bill reduction)", 0.0, 10.0),
        build_scenario("balanced_optimization", "Balanced Wealth Optimization (15% disc + 10% recurring)", 15.0, 10.0),
    ]

    # Clean up None values in action lists
    for alt in alternatives:
        alt["actions"] = [a for a in alt["actions"] if a is not None]

    # Select best scenario by monthly surplus improvement
    best_scenario = max(alternatives, key=lambda s: s["monthly_savings_improvement"])
    savings_diff_vs_baseline = {
        f"{h}_months": round(best_scenario["projected_accumulated_savings"][f"{h}_months"] - baseline_projections[f"{h}_months"], 2)
        for h in horizons
    }

    return {
        "user_id": user_id,
        "baseline_scenario": baseline_scenario,
        "alternative_scenarios": alternatives,
        "recommended_scenario": best_scenario["name"],
        "recommended_scenario_id": best_scenario["scenario_id"],
        "monthly_extra_cash_flow": best_scenario["monthly_savings_improvement"],
        "projected_savings_difference": savings_diff_vs_baseline,
        "key_changes": best_scenario["actions"],
        "assumptions": [
            "Projections assume steady monthly baseline income and constant cost of living.",
            "Projections calculate raw nominal cash surplus accumulation without speculative investment return assumptions.",
            "Any saved capital is assumed to be preserved without additional debt incurrence.",
        ],
        "limitations": [
            "Projections are hypothetical mathematical scenarios, NOT guarantees of future wealth.",
            "Does not incorporate inflation, tax adjustments, or unexpected emergency costs.",
            "Lifestyle cutbacks may not be feasible indefinitely in actual practice.",
        ],
    }
