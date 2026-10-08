import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.responsible_ai import (
    check_data_sufficiency,
    sanitize_planning_inputs,
    attach_responsible_ai_governance,
    RESPONSIBLE_AI_DISCLAIMER,
)


def test_data_sufficiency_checks():
    # Empty DataFrame
    is_ok, err = check_data_sufficiency(pd.DataFrame())
    assert not is_ok
    assert "No financial" in err

    # Too few months
    short_df = pd.DataFrame([{"month": "2025-01", "monthly_expenses": 1000.0}])
    is_ok, err = check_data_sufficiency(short_df, min_months=3)
    assert not is_ok
    assert "Insufficient history" in err

    # Valid months
    valid_df = pd.DataFrame([
        {"month": "2025-01", "monthly_expenses": 1000.0},
        {"month": "2025-02", "monthly_expenses": 1100.0},
        {"month": "2025-03", "monthly_expenses": 1200.0},
    ])
    is_ok, err = check_data_sufficiency(valid_df, min_months=3)
    assert is_ok
    assert err is None


def test_sanitize_planning_inputs():
    # Invalid inputs
    raw = {
        "risk_tolerance": "ultra_yolo_gambler",
        "has_emergency_fund": "true",
        "target_savings": -5000.0,
    }
    cleaned = sanitize_planning_inputs(raw)

    assert cleaned["risk_tolerance"] == "moderate"  # Fallback to safe default
    assert cleaned["has_emergency_fund"] is True
    assert cleaned["target_savings"] == 0.0  # Clamped to non-negative


def test_governance_attachment():
    payload = {"status": "success", "data": [1, 2, 3]}
    governed = attach_responsible_ai_governance(payload)

    assert "governance" in governed
    gov = governed["governance"]
    assert gov["is_autonomous_advisor"] is False
    assert gov["is_transaction_execution_enabled"] is False
    assert gov["is_guaranteed_return"] is False
    assert "educational" in gov["disclaimer"].lower()
