from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import SummaryResponse, CategorySpendingResponse, CategorySpending
from ml.feature_engineering import calculate_overall_summary, calculate_category_spending, calculate_monthly_features
from ml.behavior_analysis import analyze_financial_behavior

router = APIRouter(tags=["Analytics & Summary"])

PROCESSED_DATA_PATH = Path("data/processed/cleaned_transactions.csv")


def get_transactions_dataframe(db: Session, user_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieve transactions as a pandas DataFrame from DB or processed CSV fallback."""
    query = db.query(Transaction)
    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)
    records = query.all()

    if records:
        data = [
            {
                "transaction_id": r.transaction_id,
                "user_id": r.user_id,
                "date": r.date,
                "description": r.description,
                "amount": r.amount,
                "transaction_type": r.transaction_type,
                "category": r.category,
            }
            for r in records
        ]
        return pd.DataFrame(data)

    # Fallback to processed CSV if database is not yet populated
    if PROCESSED_DATA_PATH.exists():
        df = pd.read_csv(PROCESSED_DATA_PATH)
        if user_id is not None and not df.empty:
            df = df[df["user_id"] == user_id]
        return df

    return pd.DataFrame(columns=[
        "transaction_id", "user_id", "date", "description",
        "amount", "transaction_type", "category"
    ])


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """
    Calculate and return overall financial summary:
    total income, total expenses, net cash flow, and savings rate.
    """
    df = get_transactions_dataframe(db, user_id)
    summary_data = calculate_overall_summary(df, user_id=user_id)
    return summary_data


@router.get("/categories", response_model=CategorySpendingResponse)
def get_categories(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    month: Optional[str] = Query(None, description="Filter by month YYYY-MM"),
    db: Session = Depends(get_db),
):
    """Return category-level spending breakdown calculated from actual transaction data."""
    df = get_transactions_dataframe(db, user_id)
    cat_df = calculate_category_spending(df, month=month, user_id=user_id)

    total_expense = float(cat_df["total_amount"].sum()) if not cat_df.empty else 0.0
    categories_list = [
        CategorySpending(
            category=str(row["category"]),
            total_amount=float(row["total_amount"]),
            percentage=float(row["percentage"]),
            transaction_count=int(row["transaction_count"]),
        )
        for _, row in cat_df.iterrows()
    ]

    return CategorySpendingResponse(
        categories=categories_list,
        total_expense=round(total_expense, 2),
        user_id=user_id,
    )


@router.get("/behavior")
def get_behavior_analysis(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return financial behavior indicators generated from engineered monthly features."""
    df = get_transactions_dataframe(db, user_id)
    if df.empty:
        return []

    features_df = calculate_monthly_features(df, user_id=user_id)
    indicators = analyze_financial_behavior(features_df, user_id=user_id)
    return indicators
