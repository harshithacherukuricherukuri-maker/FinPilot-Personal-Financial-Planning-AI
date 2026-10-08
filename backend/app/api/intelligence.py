import json
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.schemas.intelligence import (
    ForecastResponse,
    ForecastEvaluationResponse,
    RecommendationsResponse,
    WealthOptimizationResponse,
    InsightsResponse,
)
from ml.feature_engineering import calculate_monthly_features
from ml.budget_analysis import track_budgets, generate_sample_budgets
from ml.forecasting import forecast_expenses
from ml.forecast_evaluation import evaluate_forecasting_model, DEFAULT_EVALUATION_PATH
from ml.recommendation import (
    generate_budget_recommendations,
    generate_investment_decision_support,
)
from ml.wealth_optimization import simulate_wealth_scenarios
from ml.explainability import (
    explain_forecast,
    explain_recommendations,
    explain_wealth_optimization,
)
from ml.responsible_ai import (
    check_data_sufficiency,
    sanitize_planning_inputs,
    attach_responsible_ai_governance,
)

router = APIRouter(tags=["AI / ML Intelligence"])

PROCESSED_FEATURES_PATH = Path("data/processed/monthly_features.csv")
CLEANED_TRANSACTIONS_PATH = Path("data/processed/cleaned_transactions.csv")


def get_user_features(db: Session, user_id: Optional[int] = 1) -> pd.DataFrame:
    """Retrieve monthly feature matrix from processed features or database transactions."""
    uid = user_id if user_id is not None else 1

    # Prefer verified processed features file when present
    if PROCESSED_FEATURES_PATH.exists():
        df = pd.read_csv(PROCESSED_FEATURES_PATH)
        if uid is not None and not df.empty and uid in df["user_id"].values:
            return df[df["user_id"] == uid].copy()

    records = db.query(Transaction).filter(Transaction.user_id == uid).all()
    if records:
        tx_data = [
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
        tx_df = pd.DataFrame(tx_data)
        features_df = calculate_monthly_features(tx_df, user_id=uid)
        # Exclude partial test upload months with fewer than 5 transactions for forecasting stability
        if not features_df.empty and "transaction_frequency" in features_df.columns:
            features_df = features_df[features_df["transaction_frequency"] >= 5].copy()
        return features_df

    return pd.DataFrame()


@router.get("/forecast", response_model=ForecastResponse)
def get_expense_forecast(
    user_id: Optional[int] = Query(1, description="Target user ID"),
    horizon: int = Query(3, ge=1, le=12, description="Forecast horizon in months"),
    db: Session = Depends(get_db),
):
    """Generate chronological time-series expense forecast with category breakdowns and 95% confidence intervals."""
    features_df = get_user_features(db, user_id=user_id)
    is_sufficient, err_msg = check_data_sufficiency(features_df, min_months=4)
    if not is_sufficient:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to generate forecast: {err_msg}",
        )

    forecast_data = forecast_expenses(features_df, user_id=user_id, horizon=horizon)
    forecast_with_gov = attach_responsible_ai_governance(forecast_data)
    return forecast_with_gov


@router.get("/forecast/evaluation", response_model=ForecastEvaluationResponse)
def get_forecast_evaluation(
    user_id: Optional[int] = Query(1, description="Target user ID"),
    test_months: int = Query(3, ge=1, le=6, description="Number of holdout validation months"),
    db: Session = Depends(get_db),
):
    """Retrieve chronological out-of-time forecast evaluation metrics (MAE, RMSE, MAPE)."""
    features_df = get_user_features(db, user_id=user_id)
    is_sufficient, err_msg = check_data_sufficiency(features_df, min_months=test_months + 3)
    if not is_sufficient:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to evaluate forecast: {err_msg}",
        )

    eval_data = evaluate_forecasting_model(
        features_df,
        user_id=user_id,
        test_months_count=test_months,
        save_path=DEFAULT_EVALUATION_PATH,
    )
    return eval_data


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(
    user_id: Optional[int] = Query(1, description="Target user ID"),
    risk_tolerance: str = Query("moderate", description="User risk preference: conservative, moderate, aggressive"),
    has_emergency_fund: bool = Query(False, description="Whether user already maintains a dedicated liquid emergency fund"),
    db: Session = Depends(get_db),
):
    """Generate dynamic, evidence-grounded budgeting advice and responsible investment decision support."""
    features_df = get_user_features(db, user_id=user_id)
    if features_df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No financial records found for user_id={user_id}.",
        )

    # Compile budget performance context
    budget_report = None
    records = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if records:
        tx_df = pd.DataFrame([{"transaction_id": r.transaction_id, "user_id": r.user_id, "date": r.date, "description": r.description, "amount": r.amount, "transaction_type": r.transaction_type, "category": r.category} for r in records])
        b_df = generate_sample_budgets(tx_df, user_id=user_id)
        budget_report = track_budgets(tx_df, b_df, user_id=user_id)

    # Budget recommendations
    budget_recs = generate_budget_recommendations(features_df, budget_report=budget_report, user_id=user_id)

    # Investment decision support
    sanitized_planning = sanitize_planning_inputs({
        "risk_tolerance": risk_tolerance,
        "has_emergency_fund": has_emergency_fund,
    })
    inv_support = generate_investment_decision_support(
        features_df,
        user_id=user_id,
        user_planning_input=sanitized_planning,
    )

    response_payload = {
        "user_id": user_id,
        "budget_recommendations": budget_recs,
        "investment_decision_support": inv_support,
    }
    return attach_responsible_ai_governance(response_payload)


@router.get("/wealth-optimization", response_model=WealthOptimizationResponse)
def get_wealth_optimization(
    user_id: Optional[int] = Query(1, description="Target user ID"),
    db: Session = Depends(get_db),
):
    """Execute scenario-based wealth optimization simulations across 6, 12, 24, and 36-month planning horizons."""
    features_df = get_user_features(db, user_id=user_id)
    if features_df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No financial records found for user_id={user_id}.",
        )

    optimization_data = simulate_wealth_scenarios(features_df, user_id=user_id)
    return attach_responsible_ai_governance(optimization_data)


@router.get("/insights", response_model=InsightsResponse)
def get_financial_insights(
    user_id: Optional[int] = Query(1, description="Target user ID"),
    db: Session = Depends(get_db),
):
    """Provide comprehensive explainability traces linking model forecasts, scenarios, and advice to evidence."""
    features_df = get_user_features(db, user_id=user_id)
    if features_df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No financial records found for user_id={user_id}.",
        )

    # 1. Forecast & explanation
    fc_data = forecast_expenses(features_df, user_id=user_id, horizon=3)
    ev_data = evaluate_forecasting_model(features_df, user_id=user_id, test_months_count=3, save_path=None)
    fc_explanation = explain_forecast(features_df, fc_data, ev_data, user_id=user_id)

    # 2. Wealth optimization & explanation
    opt_data = simulate_wealth_scenarios(features_df, user_id=user_id)
    opt_explanation = explain_wealth_optimization(opt_data)

    # 3. Recommendations & explanation
    budget_recs = generate_budget_recommendations(features_df, user_id=user_id)
    recs_explanation = explain_recommendations(budget_recs)

    insights_payload = {
        "user_id": user_id,
        "forecast_explanation": fc_explanation,
        "wealth_explanation": opt_explanation,
        "recommendations_explanation": recs_explanation,
    }
    return attach_responsible_ai_governance(insights_payload)
