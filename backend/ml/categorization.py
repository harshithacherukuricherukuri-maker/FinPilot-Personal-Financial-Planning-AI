import re
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Optional
import pandas as pd


class BaseCategorizer(ABC):
    """Abstract base class for transaction categorizers to enable swapping with ML models."""

    @abstractmethod
    def categorize(self, description: str, amount: Optional[float] = None) -> Tuple[str, str]:
        """Categorize a transaction based on description and optional amount."""
        pass


class RuleBasedCategorizer(BaseCategorizer):
    """
    Transparent, extensible rule-based categorizer mapping description keywords
    to financial categories with traceable reasoning.
    """

    DEFAULT_RULES: List[Dict[str, Any]] = [
        # Income
        {
            "category": "Income",
            "keywords": ["salary", "freelance", "bonus", "dividend", "interest", "paycheck", "consulting"],
            "rule_name": "rule_income_keyword",
        },
        # Housing
        {
            "category": "Housing",
            "keywords": ["rent", "maintenance", "mortgage", "housing", "property tax", "hoa"],
            "rule_name": "rule_housing_keyword",
        },
        # Food
        {
            "category": "Food",
            "keywords": [
                "grocery", "supermarket", "restaurant", "food delivery", "cafe", "coffee",
                "bakery", "dining", "uber eats", "doordash", "swiggy", "zomato", "mart", "market"
            ],
            "rule_name": "rule_food_keyword",
        },
        # Transport
        {
            "category": "Transport",
            "keywords": ["fuel", "gas", "petrol", "diesel", "bus", "cab", "metro", "train", "uber", "lyft", "transit", "taxi", "toll", "parking"],
            "rule_name": "rule_transport_keyword",
        },
        # Utilities
        {
            "category": "Utilities",
            "keywords": ["electricity", "water bill", "internet", "broadband", "mobile bill", "utility", "trash", "power", "wifi"],
            "rule_name": "rule_utilities_keyword",
        },
        # Healthcare
        {
            "category": "Healthcare",
            "keywords": ["pharmacy", "doctor", "medical", "clinic", "hospital", "dental", "medicine", "health", "prescription", "lab"],
            "rule_name": "rule_healthcare_keyword",
        },
        # Subscription
        {
            "category": "Subscription",
            "keywords": ["netflix", "spotify", "cloud subscription", "hulu", "disney", "prime", "apple music", "youtube premium", "icloud", "chatgpt"],
            "rule_name": "rule_subscription_keyword",
        },
        # Entertainment
        {
            "category": "Entertainment",
            "keywords": ["movie", "cinema", "events", "games", "gaming", "steam", "playstation", "theater", "concert", "amusement"],
            "rule_name": "rule_entertainment_keyword",
        },
        # Shopping
        {
            "category": "Shopping",
            "keywords": ["clothing", "electronics", "household shopping", "apparel", "footwear", "shoes", "fashion", "mall", "retail", "amazon"],
            "rule_name": "rule_shopping_keyword",
        },
    ]

    def __init__(self, custom_rules: Optional[List[Dict]] = None):
        rules = custom_rules or self.DEFAULT_RULES
        self.compiled_rules = []
        for r in rules:
            pattern = re.compile(
                r"\b(" + "|".join(re.escape(k) for k in r["keywords"]) + r")\b",
                re.IGNORECASE,
            )
            self.compiled_rules.append({
                "category": r["category"],
                "pattern": pattern,
                "rule_name": r["rule_name"],
            })

    def categorize(self, description: str, amount: Optional[float] = None) -> Tuple[str, str]:
        """
        Assign category based on matching keywords in description.
        Returns: (category, reason)
        """
        desc_clean = str(description).strip()
        for rule in self.compiled_rules:
            match = rule["pattern"].search(desc_clean)
            if match:
                matched_kw = match.group(0)
                return rule["category"], f"Matched '{matched_kw}' via {rule['rule_name']}"

        return "Other", "Default fallback (no rule matched)"


def categorize_dataframe(
    df: pd.DataFrame,
    categorizer: Optional[BaseCategorizer] = None,
    overwrite_existing: bool = False,
) -> pd.DataFrame:
    """
    Categorize all transactions in a DataFrame while preserving transaction_id and all attributes.
    If 'category' is already present and valid, retains it or fills missing/generic entries.
    """
    df = df.copy()
    engine = categorizer or RuleBasedCategorizer()

    categories = []
    rules = []

    for _, row in df.iterrows():
        existing_cat = str(row.get("category", "")).strip().capitalize()
        desc = row.get("description", "")
        amount = row.get("amount", None)

        if not overwrite_existing and existing_cat and existing_cat != "Nan" and existing_cat != "Other":
            categories.append(existing_cat)
            rules.append("Preserved source category")
        else:
            cat, reason = engine.categorize(desc, amount)
            categories.append(cat)
            rules.append(reason)

    df["category"] = categories
    df["categorization_rule"] = rules
    return df
