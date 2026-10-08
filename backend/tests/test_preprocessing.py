import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import date

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.preprocessing import (
    clean_dataset,
    validate_required_columns,
    convert_dates,
    convert_amounts,
    detect_duplicates,
    validate_transaction_types,
    REQUIRED_COLUMNS,
)


def sample_valid_df():
    return pd.DataFrame([
        {
            "transaction_id": "TXN-001",
            "user_id": 1,
            "date": "2025-01-05",
            "description": "Salary Deposit",
            "amount": 5000.0,
            "transaction_type": "income",
            "category": "Income",
        },
        {
            "transaction_id": "TXN-002",
            "user_id": 1,
            "date": "2025-01-06",
            "description": "Grocery Store",
            "amount": 125.50,
            "transaction_type": "expense",
            "category": "Food",
        },
    ])


def test_required_column_validation_success():
    df = sample_valid_df()
    # Should not raise
    validate_required_columns(df)


def test_required_column_validation_failure():
    df = pd.DataFrame({"transaction_id": ["TXN-001"], "amount": [50.0]})
    with pytest.raises(ValueError) as excinfo:
        validate_required_columns(df)
    assert "Missing required columns" in str(excinfo.value)


def test_date_conversion_valid_and_invalid():
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "date": ["2025-03-15", "invalid-date-string"],
    })
    res_df, valid_mask = convert_dates(df)
    assert valid_mask.iloc[0] is True or bool(valid_mask.iloc[0])
    assert bool(valid_mask.iloc[1]) is False
    assert res_df["date"].iloc[0] == date(2025, 3, 15)


def test_amount_conversion():
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3", "T4"],
        "amount": ["150.25", 0, -25.50, "not_a_number"],
    })
    res_df, valid_mask = convert_amounts(df)
    assert bool(valid_mask.iloc[0]) is True
    assert res_df["amount"].iloc[0] == 150.25
    assert bool(valid_mask.iloc[1]) is False  # Zero amount is invalid
    assert bool(valid_mask.iloc[2]) is False  # Negative amount is invalid
    assert bool(valid_mask.iloc[3]) is False  # Non-numeric is invalid


def test_duplicate_detection():
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T1"],
    })
    duplicates = detect_duplicates(df)
    assert bool(duplicates.iloc[0]) is False
    assert bool(duplicates.iloc[1]) is False
    assert bool(duplicates.iloc[2]) is True


def test_transaction_type_validation():
    df = pd.DataFrame({
        "transaction_type": ["income", "Expense", "INCOME", "transfer", "invalid"],
    })
    valid_types = validate_transaction_types(df)
    assert bool(valid_types.iloc[0]) is True
    assert bool(valid_types.iloc[1]) is True
    assert bool(valid_types.iloc[2]) is True
    assert bool(valid_types.iloc[3]) is False
    assert bool(valid_types.iloc[4]) is False


def test_clean_dataset_pipeline_full():
    raw_df = pd.DataFrame([
        # Valid income
        {"transaction_id": "T1", "user_id": 1, "date": "2025-01-01", "description": "Salary", "amount": 4000, "transaction_type": "income", "category": "Income"},
        # Valid expense
        {"transaction_id": "T2", "user_id": 1, "date": "2025-01-02", "description": "Groceries", "amount": 100, "transaction_type": "expense", "category": "Food"},
        # Duplicate T1
        {"transaction_id": "T1", "user_id": 1, "date": "2025-01-01", "description": "Salary", "amount": 4000, "transaction_type": "income", "category": "Income"},
        # Invalid amount (negative)
        {"transaction_id": "T3", "user_id": 1, "date": "2025-01-03", "description": "Refund", "amount": -50, "transaction_type": "expense", "category": "Shopping"},
        # Missing date
        {"transaction_id": "T4", "user_id": 1, "date": None, "description": "Book", "amount": 25, "transaction_type": "expense", "category": "Shopping"},
        # Invalid transaction type
        {"transaction_id": "T5", "user_id": 1, "date": "2025-01-04", "description": "Transfer", "amount": 200, "transaction_type": "transfer", "category": "Other"},
    ])

    cleaned, report, rejected = clean_dataset(raw_df)

    assert report["input_record_count"] == 6
    assert report["cleaned_record_count"] == 2
    assert report["rejected_record_count"] == 4
    assert len(cleaned) == 2
    assert set(cleaned["transaction_id"]) == {"T1", "T2"}
    assert len(rejected) == 4
    assert "T1" in rejected["transaction_id"].values


def test_clean_dataset_empty():
    empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    cleaned, report, rejected = clean_dataset(empty_df)
    assert report["input_record_count"] == 0
    assert report["cleaned_record_count"] == 0
    assert cleaned.empty
