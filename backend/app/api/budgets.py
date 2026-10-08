from pathlib import Path
from typing import Optional, List
import pandas as pd
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetResponse, BudgetCreate, BudgetTrackingResponse
from ml.budget_analysis import track_budgets, generate_sample_budgets

router = APIRouter(prefix="/budget", tags=["Budgets"])

PROCESSED_DATA_PATH = Path("data/processed/cleaned_transactions.csv")


@router.get("", response_model=BudgetTrackingResponse)
def get_budget_tracking(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """
    Calculate and return budget tracking results:
    budget amount, actual spending, variance, remaining budget, and overspending status.
    """
    # 1. Fetch transactions
    tx_query = db.query(Transaction)
    if user_id is not None:
        tx_query = tx_query.filter(Transaction.user_id == user_id)
    tx_records = tx_query.all()

    if tx_records:
        t_df = pd.DataFrame([
            {
                "transaction_id": r.transaction_id,
                "user_id": r.user_id,
                "date": r.date,
                "description": r.description,
                "amount": r.amount,
                "transaction_type": r.transaction_type,
                "category": r.category,
            }
            for r in tx_records
        ])
    elif PROCESSED_DATA_PATH.exists():
        t_df = pd.read_csv(PROCESSED_DATA_PATH)
        if user_id is not None and not t_df.empty:
            t_df = t_df[t_df["user_id"] == user_id]
    else:
        t_df = pd.DataFrame()

    # 2. Fetch budgets
    b_query = db.query(Budget)
    if user_id is not None:
        b_query = b_query.filter(Budget.user_id == user_id)
    if month is not None:
        b_query = b_query.filter(Budget.month == month)
    b_records = b_query.all()

    if b_records:
        b_df = pd.DataFrame([
            {
                "user_id": r.user_id,
                "category": r.category,
                "month": r.month,
                "budget_amount": r.budget_amount,
            }
            for r in b_records
        ])
    elif not t_df.empty:
        # If no explicit budget table rows in DB, generate benchmark budget from transactions
        b_df = generate_sample_budgets(t_df, user_id=user_id)
    else:
        b_df = pd.DataFrame()

    tracking_results = track_budgets(t_df, b_df, month=month, user_id=user_id)
    return tracking_results


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: BudgetCreate,
    db: Session = Depends(get_db),
):
    """Create or update a budget target for a user and category."""
    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == budget_in.user_id,
            Budget.category == budget_in.category,
            Budget.month == budget_in.month,
        )
        .first()
    )

    if existing:
        existing.budget_amount = budget_in.budget_amount
        db.commit()
        db.refresh(existing)
        return existing

    new_budget = Budget(
        user_id=budget_in.user_id,
        category=budget_in.category,
        month=budget_in.month,
        budget_amount=budget_in.budget_amount,
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget
