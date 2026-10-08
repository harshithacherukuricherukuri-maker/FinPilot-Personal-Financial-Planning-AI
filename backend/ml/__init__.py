import sys
from pathlib import Path

# Ensure backend directory is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.preprocessing import (
    clean_dataset,
    load_data,
    save_cleaned_data,
    validate_required_columns,
    detect_duplicates,
    convert_dates,
    convert_amounts,
    validate_transaction_types,
)
from ml.categorization import (
    BaseCategorizer,
    RuleBasedCategorizer,
    categorize_dataframe,
)
from ml.feature_engineering import (
    calculate_monthly_features,
    calculate_category_spending,
    calculate_overall_summary,
    save_monthly_features,
)
from ml.behavior_analysis import (
    analyze_financial_behavior,
    BehaviorThresholds,
)
from ml.budget_analysis import (
    track_budgets,
    generate_sample_budgets,
)
from ml.forecasting import (
    ExpenseForecaster,
    forecast_expenses,
    train_and_save_forecast_model,
    load_forecasting_model,
)
from ml.forecast_evaluation import (
    evaluate_forecasting_model,
)
from ml.recommendation import (
    generate_budget_recommendations,
    generate_investment_decision_support,
)
from ml.wealth_optimization import (
    simulate_wealth_scenarios,
)
from ml.explainability import (
    explain_forecast,
    explain_recommendations,
    explain_wealth_optimization,
)
from ml.responsible_ai import (
    check_data_sufficiency,
    sanitize_planning_inputs,
    attach_responsible_ai_governance,
    RESPONSIBLE_AI_DISCLAIMER,
)

__all__ = [
    "clean_dataset",
    "load_data",
    "save_cleaned_data",
    "validate_required_columns",
    "detect_duplicates",
    "convert_dates",
    "convert_amounts",
    "validate_transaction_types",
    "BaseCategorizer",
    "RuleBasedCategorizer",
    "categorize_dataframe",
    "calculate_monthly_features",
    "calculate_category_spending",
    "calculate_overall_summary",
    "save_monthly_features",
    "analyze_financial_behavior",
    "BehaviorThresholds",
    "track_budgets",
    "generate_sample_budgets",
    "ExpenseForecaster",
    "forecast_expenses",
    "train_and_save_forecast_model",
    "load_forecasting_model",
    "evaluate_forecasting_model",
    "generate_budget_recommendations",
    "generate_investment_decision_support",
    "simulate_wealth_scenarios",
    "explain_forecast",
    "explain_recommendations",
    "explain_wealth_optimization",
    "check_data_sufficiency",
    "sanitize_planning_inputs",
    "attach_responsible_ai_governance",
    "RESPONSIBLE_AI_DISCLAIMER",
]
