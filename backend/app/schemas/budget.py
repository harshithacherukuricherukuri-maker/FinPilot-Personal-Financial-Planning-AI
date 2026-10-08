from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class BudgetBase(BaseModel):
    user_id: int
    category: str
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Format: YYYY-MM")
    budget_amount: float = Field(gt=0, description="Budget amount must be positive")


class BudgetCreate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetTrackingItem(BaseModel):
    category: str
    month: str
    budget_amount: float
    actual_spending: float
    variance: float
    variance_percentage: float
    remaining_budget: float
    is_overspending: bool
    status: str  # "within_budget" | "warning" | "over_budget"


class BudgetTrackingResponse(BaseModel):
    month: Optional[str] = None
    user_id: Optional[int] = None
    total_budget: float
    total_actual: float
    total_variance: float
    overall_is_overspending: bool
    overall_status: str
    categories: List[BudgetTrackingItem]
