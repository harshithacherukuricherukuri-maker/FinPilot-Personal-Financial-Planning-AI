from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ForecastItem(BaseModel):
    month: str
    step: int
    predicted_total_expense: float
    confidence_lower: float
    confidence_upper: float
    confidence_margin: float
    category_forecasts: Dict[str, float] = Field(default_factory=dict)


class ForecastResponse(BaseModel):
    forecast: List[ForecastItem]
    model: str
    horizon: int
    historical_period: Optional[str] = None
    historical_months_count: Optional[int] = None
    residual_std: Optional[float] = None
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    governance: Optional[Dict[str, Any]] = None


class ForecastEvaluationResponse(BaseModel):
    model: str
    methodology: str
    training_period: str
    training_months_count: int
    evaluation_period: str
    evaluation_months_count: int
    mae: float
    rmse: float
    mape: float
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    evaluation_timestamp: Optional[str] = None


class RecommendationItem(BaseModel):
    recommendation: str
    reason: str
    evidence: List[str]
    priority: str
    confidence: float
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class RecommendationsResponse(BaseModel):
    user_id: Optional[int] = None
    budget_recommendations: List[RecommendationItem] = Field(default_factory=list)
    investment_decision_support: Dict[str, Any] = Field(default_factory=dict)
    governance: Optional[Dict[str, Any]] = None


class WealthOptimizationResponse(BaseModel):
    user_id: Optional[int] = None
    baseline_scenario: Dict[str, Any]
    alternative_scenarios: List[Dict[str, Any]]
    recommended_scenario: str
    recommended_scenario_id: Optional[str] = None
    monthly_extra_cash_flow: float
    projected_savings_difference: Dict[str, float]
    key_changes: List[str]
    assumptions: List[str]
    limitations: List[str]
    governance: Optional[Dict[str, Any]] = None


class InsightsResponse(BaseModel):
    user_id: Optional[int] = None
    forecast_explanation: Dict[str, Any]
    wealth_explanation: Dict[str, Any]
    recommendations_explanation: List[Dict[str, Any]]
    governance: Optional[Dict[str, Any]] = None
