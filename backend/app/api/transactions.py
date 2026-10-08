import io
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionResponse, UploadResponse
from ml.preprocessing import clean_dataset

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    transaction_type: Optional[str] = Query(None, description="Filter by type (income/expense)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records offset"),
    db: Session = Depends(get_db),
):
    """Retrieve processed transaction records with optional filtering."""
    query = db.query(Transaction)

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)
    if category is not None:
        query = query.filter(Transaction.category.ilike(category))
    if transaction_type is not None:
        query = query.filter(Transaction.transaction_type.ilike(transaction_type))

    query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
    records = query.offset(offset).limit(limit).all()
    return records


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept a CSV file, validate and clean data via ML preprocessing pipeline,
    and persist new verified records into PostgreSQL.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV format file (.csv)",
        )

    content = await file.read()
    try:
        csv_buffer = io.StringIO(content.decode("utf-8"))
        raw_df = pd.read_csv(csv_buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read CSV content: {str(e)}",
        )

    try:
        cleaned_df, report, _ = clean_dataset(raw_df)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Preprocessing validation failed: {str(e)}",
        )

    # Persist cleaned transactions to PostgreSQL avoiding duplicate transaction_ids
    inserted_count = 0
    duplicate_count = 0

    if not cleaned_df.empty:
        # Verify or auto-create users if needed
        unique_users = cleaned_df["user_id"].unique()
        for uid in unique_users:
            user_exists = db.query(User).filter(User.id == int(uid)).first()
            if not user_exists:
                db_user = User(id=int(uid), name=f"User {uid}", email=f"user{uid}@finpilot.ai")
                db.add(db_user)
        db.commit()

        # Query existing transaction_ids to avoid duplicates
        incoming_ids = cleaned_df["transaction_id"].astype(str).tolist()
        existing_ids = set(
            tx_id for (tx_id,) in db.query(Transaction.transaction_id)
            .filter(Transaction.transaction_id.in_(incoming_ids))
            .all()
        )

        for _, row in cleaned_df.iterrows():
            tx_id = str(row["transaction_id"])
            if tx_id in existing_ids:
                duplicate_count += 1
                continue

            db_tx = Transaction(
                transaction_id=tx_id,
                user_id=int(row["user_id"]),
                date=row["date"],
                description=str(row["description"]),
                amount=float(row["amount"]),
                transaction_type=str(row["transaction_type"]).lower(),
                category=str(row["category"]),
            )
            db.add(db_tx)
            existing_ids.add(tx_id)
            inserted_count += 1

        db.commit()

    return UploadResponse(
        message="Transactions processed and uploaded successfully",
        records_received=report["input_record_count"],
        records_cleaned=report["cleaned_record_count"],
        records_inserted=inserted_count,
        duplicates_skipped=duplicate_count + report["duplicate_count"],
        invalid_records=report["invalid_record_count"],
    )
