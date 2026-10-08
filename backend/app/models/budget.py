from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    month = Column(String(7), index=True, nullable=False)  # YYYY-MM
    budget_amount = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    user = relationship("User", back_populates="budgets")

    __table_args__ = (
        Index("ix_budgets_user_month", "user_id", "month"),
        Index("ix_budgets_user_cat_month", "user_id", "category", "month"),
        UniqueConstraint("user_id", "category", "month", name="uq_user_category_month"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, user={self.user_id}, category='{self.category}', month='{self.month}', amount={self.budget_amount})>"
