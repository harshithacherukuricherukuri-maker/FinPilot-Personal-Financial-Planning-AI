from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class TransactionBase(BaseModel):
    transaction_id: str
    user_id: int
    date: date
    description: str
    amount: float = Field(gt=0, description="Transaction amount must be positive")
    transaction_type: str = Field(pattern="^(income|expense)$")
    category: str


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_cash_flow: float
    savings_rate: float
    transaction_count: int
    user_id: Optional[int] = None


class CategorySpending(BaseModel):
    category: str
    total_amount: float
    percentage: float
    transaction_count: int


class CategorySpendingResponse(BaseModel):
    categories: List[CategorySpending]
    total_expense: float
    user_id: Optional[int] = None


class UploadResponse(BaseModel):
    message: str
    records_received: int
    records_cleaned: int
    records_inserted: int
    duplicates_skipped: int
    invalid_records: int
