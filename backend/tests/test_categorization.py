import sys
from pathlib import Path
import pytest
import pandas as pd

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml.categorization import RuleBasedCategorizer, categorize_dataframe


@pytest.fixture
def categorizer():
    return RuleBasedCategorizer()


def test_food_categorization(categorizer):
    category, rule = categorizer.categorize("Whole Foods Grocery Store")
    assert category == "Food"
    assert "Matched 'Grocery'" in rule or "grocery" in rule.lower()

    category, _ = categorizer.categorize("Italian Restaurant Dining")
    assert category == "Food"

    category, _ = categorizer.categorize("Uber Eats Dinner Delivery")
    assert category == "Food"


def test_housing_categorization(categorizer):
    category, rule = categorizer.categorize("Monthly Apartment Rent")
    assert category == "Housing"
    assert "rent" in rule.lower()

    category, _ = categorizer.categorize("Building Maintenance Charge")
    assert category == "Housing"


def test_transport_categorization(categorizer):
    category, rule = categorizer.categorize("Shell Gas Fuel Station")
    assert category == "Transport"
    assert "fuel" in rule.lower() or "gas" in rule.lower()

    category, _ = categorizer.categorize("City Metro Pass")
    assert category == "Transport"

    category, _ = categorizer.categorize("Uber Cab Trip")
    assert category == "Transport"


def test_utility_categorization(categorizer):
    category, rule = categorizer.categorize("City Electricity Board")
    assert category == "Utilities"

    category, _ = categorizer.categorize("Home Internet Fiber Bill")
    assert category == "Utilities"

    category, _ = categorizer.categorize("Monthly Mobile Bill")
    assert category == "Utilities"


def test_subscription_categorization(categorizer):
    category, rule = categorizer.categorize("Netflix Subscription")
    assert category == "Subscription"

    category, _ = categorizer.categorize("Spotify Family Plan")
    assert category == "Subscription"

    category, _ = categorizer.categorize("Google Cloud Subscription")
    assert category == "Subscription"


def test_fallback_other(categorizer):
    category, rule = categorizer.categorize("Unknown Random Vendor XYZ")
    assert category == "Other"
    assert "Default fallback" in rule


def test_categorize_dataframe_preserves_transaction_id():
    df = pd.DataFrame([
        {"transaction_id": "T-100", "description": "Grocery Mart", "amount": 54.20},
        {"transaction_id": "T-101", "description": "Netflix", "amount": 15.99},
    ])
    result_df = categorize_dataframe(df)
    assert "transaction_id" in result_df.columns
    assert list(result_df["transaction_id"]) == ["T-100", "T-101"]
    assert list(result_df["category"]) == ["Food", "Subscription"]
    assert "categorization_rule" in result_df.columns
