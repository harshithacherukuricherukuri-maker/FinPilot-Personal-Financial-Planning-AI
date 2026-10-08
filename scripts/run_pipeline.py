import sys
import json
from pathlib import Path
import pandas as pd

# Add backend directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from ml.preprocessing import clean_dataset, save_cleaned_data
from ml.categorization import categorize_dataframe, RuleBasedCategorizer
from ml.feature_engineering import (
    calculate_monthly_features,
    calculate_overall_summary,
    save_monthly_features,
)
from ml.behavior_analysis import analyze_financial_behavior
from ml.budget_analysis import generate_sample_budgets, track_budgets


def execute_pipeline(
    input_csv: str = "data/sample/transactions.csv",
    cleaned_output_csv: str = "data/processed/cleaned_transactions.csv",
    features_output_csv: str = "data/processed/monthly_features.csv",
):
    print("=" * 60)
    print("FinPilot Financial Data Preparation Pipeline")
    print("=" * 60)

    # [1/5] Loading data
    print("\n[1/5] Loading data...")
    source_path = Path(input_csv)
    if not source_path.exists():
        print(f"Error: Input dataset not found at {source_path}")
        sys.exit(1)

    try:
        raw_df = pd.read_csv(source_path)
        print(f"  --> Successfully loaded {len(raw_df)} records from {source_path}")
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        sys.exit(1)

    # [2/5] Cleaning data
    print("\n[2/5] Cleaning and validating transactions...")
    try:
        cleaned_df, report, rejected_df = clean_dataset(raw_df)
        print(f"  --> Input record count:     {report['input_record_count']}")
        print(f"  --> Missing values flagged: {report['missing_values']}")
        print(f"  --> Duplicate IDs detected: {report['duplicate_count']}")
        print(f"  --> Invalid records:        {report['invalid_record_count']}")
        print(f"  --> Rejected record count:  {report['rejected_record_count']}")
        print(f"  --> Cleaned record count:   {report['cleaned_record_count']}")

        saved_path = save_cleaned_data(cleaned_df, cleaned_output_csv)
        print(f"  --> Saved cleaned transactions to: {saved_path}")
    except Exception as e:
        print(f"Error during data cleaning stage: {e}")
        sys.exit(1)

    # [3/5] Categorizing transactions
    print("\n[3/5] Categorizing transactions and verifying rule assignments...")
    try:
        categorized_df = categorize_dataframe(cleaned_df, categorizer=RuleBasedCategorizer())
        cat_counts = categorized_df["category"].value_counts().to_dict()
        print(f"  --> Categorized {len(categorized_df)} transactions across {len(cat_counts)} categories:")
        for cat, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      - {cat:<15}: {cnt} transactions")
        # Save updated categorized data back to cleaned destination
        save_cleaned_data(categorized_df, cleaned_output_csv)
    except Exception as e:
        print(f"Error during categorization stage: {e}")
        sys.exit(1)

    # [4/5] Generating features
    print("\n[4/5] Engineering monthly financial features...")
    try:
        features_df = calculate_monthly_features(categorized_df)
        print(f"  --> Generated monthly feature matrix: {features_df.shape[0]} user-month rows")
        feat_path = save_monthly_features(features_df, features_output_csv)
        print(f"  --> Saved monthly feature dataset to: {feat_path}")

        # Overall summary metric check
        summary = calculate_overall_summary(categorized_df)
        print("  --> Aggregate Summary:")
        print(f"      - Total Income:    ${summary['total_income']:,.2f}")
        print(f"      - Total Expenses:  ${summary['total_expenses']:,.2f}")
        print(f"      - Net Cash Flow:   ${summary['net_cash_flow']:,.2f}")
        print(f"      - Savings Rate:    {summary['savings_rate']:.2f}%")
    except Exception as e:
        print(f"Error during feature engineering stage: {e}")
        sys.exit(1)

    # [5/5] Running behavior and budget analysis
    print("\n[5/5] Running behavior analysis and budget tracking...")
    try:
        # Behavior analysis for primary user
        primary_user_id = 1
        indicators = analyze_financial_behavior(features_df, user_id=primary_user_id)
        print(f"\n  --> Behavior Indicators for User {primary_user_id} ({len(indicators)} detected):")
        for ind in indicators:
            print(f"      [{ind['indicator']}] Value: {ind['value']} ({ind['metric']})")
            print(f"        |-- {ind['interpretation']}")

        # Budget analysis
        budgets_df = generate_sample_budgets(categorized_df, user_id=primary_user_id)
        budget_report = track_budgets(categorized_df, budgets_df, user_id=primary_user_id)
        print(f"\n  --> Budget Tracking for User {primary_user_id} (Month: {budget_report['month']}):")
        print(f"      - Total Allocated Budget: ${budget_report['total_budget']:,.2f}")
        print(f"      - Total Actual Spending:  ${budget_report['total_actual']:,.2f}")
        print(f"      - Variance:               ${budget_report['total_variance']:,.2f}")
        print(f"      - Overall Status:         {budget_report['overall_status'].upper()}")
        print(f"      - Category Breakdown ({len(budget_report['categories'])} categories tracked)")
    except Exception as e:
        print(f"Error during behavior/budget analysis stage: {e}")
        sys.exit(1)

    # [6/6] Training AI/ML models & generating intelligence
    print("\n[6/6] Running AI/ML intelligence layer (Forecasting, Evaluation, Wealth Optimization)...")
    try:
        from ml.forecasting import train_and_save_forecast_model, forecast_expenses
        from ml.forecast_evaluation import evaluate_forecasting_model
        from ml.recommendation import generate_budget_recommendations, generate_investment_decision_support
        from ml.wealth_optimization import simulate_wealth_scenarios
        from ml.explainability import explain_forecast

        # Train and save model
        model_path = ROOT_DIR / "models" / "expense_forecast_model.pkl"
        train_and_save_forecast_model(features_df, user_id=primary_user_id, output_path=model_path)
        print(f"  --> Saved forecasting model artifact to: {model_path}")

        # Forecast next 3 months
        fc_data = forecast_expenses(features_df, user_id=primary_user_id, horizon=3, model_path=model_path)
        print("  --> 3-Month Expense Forecast:")
        for item in fc_data["forecast"]:
            print(f"      - {item['month']}: ${item['predicted_total_expense']:,.2f} (95% CI: ${item['confidence_lower']:,.2f} - ${item['confidence_upper']:,.2f})")

        # Evaluate forecast
        eval_path = ROOT_DIR / "models" / "forecast_evaluation.json"
        eval_metrics = evaluate_forecasting_model(features_df, user_id=primary_user_id, test_months_count=3, save_path=eval_path)
        print(f"  --> Forecast Evaluation (Holdout {eval_metrics['evaluation_period']}):")
        print(f"      - MAE:  ${eval_metrics['mae']:,.2f}")
        print(f"      - RMSE: ${eval_metrics['rmse']:,.2f}")
        print(f"      - MAPE: {eval_metrics['mape']:.2f}%")
        print(f"  --> Saved evaluation metrics to: {eval_path}")

        # Budget Recommendations
        recs = generate_budget_recommendations(features_df, budget_report=budget_report, user_id=primary_user_id)
        print(f"  --> Generated {len(recs)} budget recommendation(s):")
        for r in recs[:2]:
            print(f"      [{r['priority'].upper()}] {r['recommendation']}")

        # Investment Decision Support
        inv_support = generate_investment_decision_support(features_df, user_id=primary_user_id)
        print(f"  --> Investment Decision Support Status: {inv_support['status'].upper()}")

        # Wealth Optimization
        wealth_res = simulate_wealth_scenarios(features_df, user_id=primary_user_id)
        print(f"  --> Wealth Optimization: Recommended '{wealth_res['recommended_scenario']}'")
        print(f"      - Extra Monthly Cash Flow: +${wealth_res['monthly_extra_cash_flow']:,.2f}/mo")

    except Exception as e:
        print(f"Error during AI/ML intelligence stage: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    execute_pipeline()
