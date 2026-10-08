import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "transaction_id",
    "user_id",
    "date",
    "description",
    "amount",
    "transaction_type",
    "category",
]

VALID_TRANSACTION_TYPES = {"income", "expense"}


def load_data(file_source: Union[str, Path, pd.DataFrame]) -> pd.DataFrame:
    """Load data from a CSV file path or return a copy if already a DataFrame."""
    if isinstance(file_source, pd.DataFrame):
        return file_source.copy()
    path = Path(file_source)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found at: {path}")
    return pd.read_csv(path)


def validate_required_columns(df: pd.DataFrame, required_columns: Optional[list] = None) -> None:
    """Validate that all required columns are present in the DataFrame."""
    required = required_columns or REQUIRED_COLUMNS
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")


def normalize_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize description text: strip whitespace, collapse multi-spaces, title case."""
    df = df.copy()
    if "description" in df.columns:
        df["description"] = (
            df["description"]
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )
    return df


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize category strings: strip whitespace and standardize casing."""
    df = df.copy()
    if "category" in df.columns:
        df["category"] = (
            df["category"]
            .astype(str)
            .str.strip()
            .str.capitalize()
        )
    return df


def validate_transaction_types(df: pd.DataFrame) -> pd.Series:
    """Return boolean series where transaction_type is valid ('income' or 'expense')."""
    if "transaction_type" not in df.columns:
        return pd.Series(False, index=df.index)
    normalized = df["transaction_type"].astype(str).str.strip().str.lower()
    return normalized.isin(VALID_TRANSACTION_TYPES)


def convert_dates(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Convert date column to datetime.date, returning modified df and boolean series of validity."""
    df = df.copy()
    parsed_dates = pd.to_datetime(df["date"], errors="coerce")
    valid_dates = parsed_dates.notna()
    df["date"] = parsed_dates.dt.date
    return df, valid_dates


def convert_amounts(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Convert amount column to numeric float, returning modified df and boolean series of validity."""
    df = df.copy()
    numeric_amounts = pd.to_numeric(df["amount"], errors="coerce")
    # Amounts must be non-null and strictly positive (> 0)
    valid_amounts = numeric_amounts.notna() & (numeric_amounts > 0)
    df["amount"] = numeric_amounts.round(2)
    return df, valid_amounts


def detect_duplicates(df: pd.DataFrame) -> pd.Series:
    """Return boolean series marking duplicate records based on transaction_id."""
    return df.duplicated(subset=["transaction_id"], keep="first")


def sort_chronologically(df: pd.DataFrame) -> pd.DataFrame:
    """Sort DataFrame chronologically by date and reset index."""
    df = df.copy()
    if "date" in df.columns:
        return df.sort_values(by=["date", "transaction_id"]).reset_index(drop=True)
    return df.reset_index(drop=True)


def clean_dataset(
    file_source: Union[str, Path, pd.DataFrame]
) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """
    Execute full data cleaning & validation pipeline.
    
    Returns:
        (cleaned_df, report_dict, rejected_df)
    """
    raw_df = load_data(file_source)
    input_records = len(raw_df)

    # 1. Validate required columns
    validate_required_columns(raw_df)

    working_df = raw_df.copy()
    rejection_reasons = pd.Series("", index=working_df.index)

    # 2. Check for missing values in critical columns
    missing_mask = working_df[REQUIRED_COLUMNS].isna().any(axis=1)
    for col in REQUIRED_COLUMNS:
        col_missing = working_df[col].isna()
        rejection_reasons[col_missing] = rejection_reasons[col_missing].apply(
            lambda r, c=col: f"{r}; Missing {c}".strip("; ")
        )

    # 3. Detect duplicate transaction_ids
    duplicate_mask = detect_duplicates(working_df)
    rejection_reasons[duplicate_mask] = rejection_reasons[duplicate_mask].apply(
        lambda r: f"{r}; Duplicate transaction_id".strip("; ")
    )

    # 4. Validate & convert dates
    working_df, valid_dates = convert_dates(working_df)
    invalid_dates = ~valid_dates
    rejection_reasons[invalid_dates] = rejection_reasons[invalid_dates].apply(
        lambda r: f"{r}; Invalid date format".strip("; ")
    )

    # 5. Validate & convert amounts
    working_df, valid_amounts = convert_amounts(working_df)
    invalid_amounts = ~valid_amounts
    rejection_reasons[invalid_amounts] = rejection_reasons[invalid_amounts].apply(
        lambda r: f"{r}; Invalid amount (must be numeric > 0)".strip("; ")
    )

    # 6. Validate transaction types
    valid_types = validate_transaction_types(working_df)
    invalid_types = ~valid_types
    rejection_reasons[invalid_types] = rejection_reasons[invalid_types].apply(
        lambda r: f"{r}; Invalid transaction_type (must be income or expense)".strip("; ")
    )

    # Normalize fields
    working_df["transaction_type"] = (
        working_df["transaction_type"].astype(str).str.strip().str.lower()
    )
    working_df = normalize_descriptions(working_df)
    working_df = normalize_categories(working_df)

    # Compile rejection mask
    rejection_mask = (
        missing_mask
        | duplicate_mask
        | invalid_dates
        | invalid_amounts
        | invalid_types
    )

    # Traceable rejected records
    rejected_df = raw_df[rejection_mask].copy()
    rejected_df["rejection_reason"] = rejection_reasons[rejection_mask]

    # Valid cleaned records
    cleaned_df = working_df[~rejection_mask].copy()
    cleaned_df = sort_chronologically(cleaned_df)

    # Build report
    report: Dict[str, Any] = {
        "input_record_count": input_records,
        "missing_values": int(missing_mask.sum()),
        "duplicate_count": int(duplicate_mask.sum()),
        "invalid_record_count": int((invalid_dates | invalid_amounts | invalid_types).sum()),
        "rejected_record_count": int(rejection_mask.sum()),
        "cleaned_record_count": int(len(cleaned_df)),
    }

    return cleaned_df, report, rejected_df


def save_cleaned_data(
    cleaned_df: pd.DataFrame,
    output_path: Union[str, Path] = "data/processed/cleaned_transactions.csv"
) -> Path:
    """Save cleaned transactions to CSV destination."""
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(dest, index=False)
    return dest
