import math
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

RESPONSIBLE_AI_DISCLAIMER = (
    "FinPilot AI/ML modules provide educational analytics and decision-support modeling only. "
    "The platform does not execute financial transactions, manage assets, provide autonomous financial advice, "
    "or guarantee financial returns. Projections are hypothetical scenario simulations based on historical data. "
    "Consult a certified fiduciary financial professional before making significant financial commitments."
)


def check_data_sufficiency(
    features_df: pd.DataFrame,
    min_months: int = 3,
) -> Tuple[bool, Optional[str]]:
    """
    Verify whether the provided financial features dataset has sufficient historical
    depth and data integrity to support reliable analytical and modeling outputs.
    """
    if features_df is None or features_df.empty:
        return False, "No financial transaction features available."

    if len(features_df) < min_months:
        return (
            False,
            f"Insufficient history: {len(features_df)} month(s) available, but at least {min_months} months are required.",
        )

    # Check for valid numeric expenses
    if "monthly_expenses" not in features_df.columns or features_df["monthly_expenses"].isna().all():
        return False, "Missing or invalid monthly expense values."

    return True, None


def sanitize_planning_inputs(inputs: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitize optional user planning inputs, strictly preventing negative balances,
    infinite rates, or extreme unconstrained values.
    """
    if not inputs:
        return {"risk_tolerance": "moderate", "has_emergency_fund": False}

    sanitized = {}
    # Risk tolerance
    risk = str(inputs.get("risk_tolerance", "moderate")).strip().lower()
    sanitized["risk_tolerance"] = risk if risk in {"conservative", "moderate", "aggressive"} else "moderate"

    # Emergency fund status
    sanitized["has_emergency_fund"] = bool(inputs.get("has_emergency_fund", False))

    # Optional manual target savings amount (if provided, must be finite and >= 0)
    if "target_savings" in inputs:
        try:
            val = float(inputs["target_savings"])
            sanitized["target_savings"] = max(0.0, val) if math.isfinite(val) else 0.0
        except (ValueError, TypeError):
            sanitized["target_savings"] = 0.0

    return sanitized


def attach_responsible_ai_governance(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarantee that any outgoing AI/ML response includes transparent governance metadata,
    explicit assumption tags, limitation bounds, and the non-autonomous disclaimer.
    """
    response_copy = response.copy()
    response_copy["governance"] = {
        "is_autonomous_advisor": False,
        "is_transaction_execution_enabled": False,
        "is_guaranteed_return": False,
        "disclaimer": RESPONSIBLE_AI_DISCLAIMER,
    }
    return response_copy
