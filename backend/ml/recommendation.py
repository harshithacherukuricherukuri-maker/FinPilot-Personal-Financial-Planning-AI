import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Ensure backend directory is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))


def generate_budget_recommendations(
    features_df: pd.DataFrame,
    budget_report: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Generate dynamic, personalized budgeting recommendations derived strictly
    from actual historical financial metrics and budget performance.
    """
    if features_df.empty:
        return []

    df = features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]
        if df.empty:
            return []

    df = df.sort_values(by="month").reset_index(drop=True)
    recommendations: List[Dict[str, Any]] = []

    # Calculate actual financial baselines
    avg_income = float(df["monthly_income"].mean())
    avg_expenses = float(df["monthly_expenses"].mean())
    avg_savings_rate = float(df["savings_rate"].mean())
    recent_savings_rate = float(df["savings_rate"].iloc[-1])
    avg_recurring = float(df["recurring_spending"].mean()) if "recurring_spending" in df.columns else 0.0
    avg_discretionary = float(df["discretionary_spending"].mean()) if "discretionary_spending" in df.columns else 0.0
    avg_concentration = float(df["category_concentration"].mean()) if "category_concentration" in df.columns else 0.0
    top_cat = str(df["top_category"].iloc[-1]) if "top_category" in df.columns else "Primary Category"

    discretionary_ratio = (avg_discretionary / avg_expenses * 100.0) if avg_expenses > 0 else 0.0
    recurring_ratio = (avg_recurring / avg_expenses * 100.0) if avg_expenses > 0 else 0.0

    # 1. High Discretionary Spending Rule
    if discretionary_ratio >= 30.0:
        recommendations.append({
            "recommendation": "Review and trim discretionary lifestyle expenses.",
            "reason": f"Discretionary spending represents {discretionary_ratio:.1f}% of total monthly outflows.",
            "evidence": [
                f"Average monthly discretionary spend: ${avg_discretionary:,.2f}",
                f"Average monthly total expenses: ${avg_expenses:,.2f}",
                f"Discretionary expenditure share: {discretionary_ratio:.1f}% (Benchmark: < 30%)",
            ],
            "priority": "high" if discretionary_ratio >= 40.0 else "medium",
            "confidence": 0.88,
            "assumptions": [
                "Discretionary categories include Shopping, Entertainment, Subscriptions, and Miscellaneous.",
                "Trimming non-essential outlays frees up immediate surplus without impacting core obligations.",
            ],
            "limitations": [
                "Does not account for non-recurring life events or seasonal holiday spending.",
                "Spending reduction feasibility depends on individual lifestyle preferences.",
            ],
        })

    # 2. Declining or Depressed Savings Rate Rule
    if recent_savings_rate < 15.0 or (len(df) >= 3 and recent_savings_rate < avg_savings_rate - 5.0):
        recommendations.append({
            "recommendation": "Address recent savings rate compression.",
            "reason": f"Recent savings rate of {recent_savings_rate:.1f}% is below the healthy baseline benchmark.",
            "evidence": [
                f"Most recent month savings rate: {recent_savings_rate:.1f}%",
                f"Historical average savings rate: {avg_savings_rate:.1f}%",
                f"Monthly net cash flow: ${float(df['monthly_net_cash_flow'].iloc[-1]):,.2f}",
            ],
            "priority": "high",
            "confidence": 0.92,
            "assumptions": [
                "Assumes recent income has posted completely for the period.",
                "Benchmark assumes standard 20% target savings rate recommended by financial guidelines.",
            ],
            "limitations": [
                "Temporary income timing mismatches or delays can distort monthly savings rates.",
            ],
        })

    # 3. High Category Concentration Rule
    if avg_concentration >= 35.0:
        recommendations.append({
            "recommendation": f"Monitor heavy financial exposure in {top_cat}.",
            "reason": f"A single category ({top_cat}) accounts for {avg_concentration:.1f}% of monthly expenditure.",
            "evidence": [
                f"Top expenditure category: {top_cat}",
                f"Category concentration ratio: {avg_concentration:.1f}%",
                f"Total monthly expense baseline: ${avg_expenses:,.2f}",
            ],
            "priority": "medium",
            "confidence": 0.85,
            "assumptions": [
                "Single category concentration above 35% reduces flexibility to absorb secondary expense spikes.",
            ],
            "limitations": [
                "Essential costs like metropolitan rent or mortgage are often inherently high-concentration.",
            ],
        })

    # 4. Recurring Commitments Overhead Rule
    if recurring_ratio >= 45.0:
        recommendations.append({
            "recommendation": "Audit recurring fixed commitments and subscription services.",
            "reason": f"Committed recurring expenses consume {recurring_ratio:.1f}% of your total budget.",
            "evidence": [
                f"Average monthly recurring commitments: ${avg_recurring:,.2f}",
                f"Recurring expenditure ratio: {recurring_ratio:.1f}% (Benchmark: < 45%)",
            ],
            "priority": "medium",
            "confidence": 0.82,
            "assumptions": [
                "Recurring expenses include Housing, Utilities, and Subscriptions.",
                "Unused or legacy subscriptions can often be renegotiated or cancelled.",
            ],
            "limitations": [
                "Fixed leases and utility rates cannot be altered immediately in the short term.",
            ],
        })

    # 5. Positive Cash Flow Optimization Rule
    if recent_savings_rate >= 25.0 and float(df["monthly_net_cash_flow"].iloc[-1]) > 500.0:
        net_surplus = float(df["monthly_net_cash_flow"].iloc[-1])
        recommendations.append({
            "recommendation": "Direct positive monthly cash surplus into systematic reserves.",
            "reason": f"Strong net cash flow of ${net_surplus:,.2f} provides room to build emergency reserves or goals.",
            "evidence": [
                f"Recent monthly net surplus: ${net_surplus:,.2f}",
                f"Recent savings rate: {recent_savings_rate:.1f}%",
            ],
            "priority": "medium",
            "confidence": 0.90,
            "assumptions": [
                "Assumes surplus is not already earmarked for impending annual tax or insurance obligations.",
            ],
            "limitations": [
                "Surplus may fluctuate if income includes variable freelance or bonus payments.",
            ],
        })

    # 6. Budget Overspending Rule (if budget tracking context provided)
    if budget_report and budget_report.get("overall_is_overspending"):
        over_cats = [
            c["category"] for c in budget_report.get("categories", [])
            if c.get("is_overspending")
        ]
        recommendations.append({
            "recommendation": "Rebalance active category budget allocations.",
            "reason": f"Actual monthly expenses exceeded budget targets in {', '.join(over_cats) if over_cats else 'tracked categories'}.",
            "evidence": [
                f"Total allocated budget: ${budget_report.get('total_budget', 0):,.2f}",
                f"Total actual expenditure: ${budget_report.get('total_actual', 0):,.2f}",
                f"Budget variance: +${budget_report.get('total_variance', 0):,.2f}",
            ],
            "priority": "high",
            "confidence": 0.94,
            "assumptions": [
                "Existing budget caps were set realistically relative to cost of living.",
            ],
            "limitations": [
                "Overspending might reflect necessary seasonal surges rather than systemic budget drift.",
            ],
        })

    return recommendations


def generate_investment_decision_support(
    features_df: pd.DataFrame,
    user_id: Optional[int] = None,
    user_planning_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Provide educational, decision-support investment guidance.
    
    RESPONSIBLE AI RULES:
    - NOT autonomous financial advice.
    - Does NOT execute transactions, connect to brokerages, guarantee returns, or fabricate portfolio balances.
    - Explicitly returns 'Insufficient financial information' if cash flows or emergency reserves are deficient.
    """
    if features_df.empty:
        return {
            "status": "insufficient_data",
            "message": "Insufficient financial information for investment-oriented recommendation.",
            "reasons": ["No historical transaction records available to evaluate cash flow viability."],
            "recommendations": [],
            "disclaimer": "FinPilot provides educational decision support only and does not execute investment transactions.",
        }

    df = features_df.copy()
    if user_id is not None:
        df = df[df["user_id"] == user_id]
        if df.empty:
            return {
                "status": "insufficient_data",
                "message": "Insufficient financial information for investment-oriented recommendation.",
                "reasons": ["No transaction records for the requested user."],
                "recommendations": [],
                "disclaimer": "FinPilot provides educational decision support only and does not execute investment transactions.",
            }

    df = df.sort_values(by="month").reset_index(drop=True)
    avg_income = float(df["monthly_income"].mean())
    avg_expenses = float(df["monthly_expenses"].mean())
    avg_net_surplus = float(df["monthly_net_cash_flow"].mean())
    avg_savings_rate = float(df["savings_rate"].mean())

    # Check financial foundation prerequisites
    if avg_net_surplus <= 0 or avg_income <= 0:
        return {
            "status": "insufficient_data",
            "message": "Insufficient financial information for investment-oriented recommendation.",
            "reasons": [
                "Net monthly cash flow is zero or negative across the observation period.",
                "Investment strategies require a sustainable monthly surplus to avoid compounding debt.",
            ],
            "recommendations": [
                {
                    "guidance": "Prioritize cash flow stabilization before exploring market investments.",
                    "rationale": "Investing when expenses exceed income exposes capital to forced liquidation during market drawdowns.",
                    "evidence": [
                        f"Average monthly expenses (${avg_expenses:,.2f}) equal or exceed income (${avg_income:,.2f}).",
                        f"Average net monthly cash flow: ${avg_net_surplus:,.2f}",
                    ],
                    "priority": "critical",
                    "confidence": 0.95,
                    "assumptions": ["Assumes recorded transaction data captures all primary living expenses."],
                    "limitations": ["External liquidity or savings held outside the platform cannot be verified."],
                }
            ],
            "disclaimer": "Educational decision-support only. Not investment advice or an offer to trade securities.",
        }

    # Safe evaluation of emergency readiness
    planning = user_planning_input or {}
    has_emergency_fund = planning.get("has_emergency_fund", False)
    risk_tolerance = planning.get("risk_tolerance", "moderate").lower()

    # Recommended 3 to 6 months emergency reserve target
    emergency_target_3m = round(avg_expenses * 3.0, 2)
    emergency_target_6m = round(avg_expenses * 6.0, 2)

    decision_guidance = []

    # Guidance 1: Emergency Reserve Readiness
    if not has_emergency_fund:
        decision_guidance.append({
            "guidance": "Build a liquid 3 to 6-month emergency reserve prior to capital market allocation.",
            "rationale": "A dedicated emergency cushion prevents premature liquidation of volatile long-term investments.",
            "evidence": [
                f"Average monthly baseline living expenses: ${avg_expenses:,.2f}",
                f"Estimated 3-month emergency reserve target: ${emergency_target_3m:,.2f}",
                f"Estimated 6-month emergency reserve target: ${emergency_target_6m:,.2f}",
                f"Current average monthly surplus: ${avg_net_surplus:,.2f}",
            ],
            "priority": "high",
            "confidence": 0.92,
            "assumptions": [
                "Assumes emergency funds are held in highly liquid, capital-preserving instruments (e.g., High-Yield Savings or FDIC-insured accounts).",
            ],
            "limitations": [
                "Does not account for existing liquid reserves held in external financial institutions.",
            ],
        })

    # Guidance 2: Long-Term Educational Asset Allocation Principles
    allocation_notes = {
        "conservative": "Focus on capital preservation with higher fixed-income / treasury orientation.",
        "moderate": "Balanced growth and capital preservation (e.g., broad market total index funds and bonds).",
        "aggressive": "Equity-heavy orientation suitable for longer horizons (>7-10 years) with higher volatility tolerance.",
    }.get(risk_tolerance, "Balanced broad-market diversification.")

    decision_guidance.append({
        "guidance": f"Review diversified long-term asset allocation aligned with your '{risk_tolerance}' profile.",
        "rationale": "Cost-efficient, diversified index strategies historically capture market growth while dampening idiosyncratic risk.",
        "evidence": [
            f"Average monthly investable surplus: ${avg_net_surplus:,.2f}",
            f"Average savings rate: {avg_savings_rate:.1f}%",
            f"Declared risk preference: {risk_tolerance}",
        ],
        "priority": "medium",
        "confidence": 0.85,
        "assumptions": [
            "Assumes a long investment horizon (>5 years) without impending short-term withdrawal needs.",
            f"Assumes alignment with a {risk_tolerance} risk profile: {allocation_notes}",
        ],
        "limitations": [
            "Past market performance does not guarantee future results.",
            "All market investments carry risk of principal loss.",
            "FinPilot does not manage assets, execute orders, or provide fiduciary financial planning.",
        ],
    })

    # Guidance 3: Professional Consultation
    decision_guidance.append({
        "guidance": "Consult a certified, fee-only fiduciary financial advisor.",
        "rationale": "A qualified human professional can customize tax-advantaged accounts (e.g. 401(k), IRA) and legal estate structures.",
        "evidence": ["Platform algorithms provide educational analytics and cannot substitute for personalized fiduciary advice."],
        "priority": "low",
        "confidence": 0.99,
        "assumptions": ["A holistic financial plan requires reviewing taxes, insurance, and retirement liabilities."],
        "limitations": ["Advisor fees and availability vary by jurisdiction."],
    })

    return {
        "status": "ready",
        "monthly_investable_surplus": avg_net_surplus,
        "average_monthly_expenses": avg_expenses,
        "emergency_target_3_months": emergency_target_3m,
        "emergency_target_6_months": emergency_target_6m,
        "risk_profile_evaluated": risk_tolerance,
        "recommendations": decision_guidance,
        "disclaimer": "Educational decision-support only. Not autonomous financial advice, guarantee of returns, or solicitation.",
    }
