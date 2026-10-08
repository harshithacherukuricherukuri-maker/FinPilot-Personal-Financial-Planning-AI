import os
import sys
import random
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd

# Add backend directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))


def generate_transactions(
    seed: int = 42,
    num_months: int = 18,
    start_date: date = date(2025, 1, 1),
    output_path: str = "data/sample/transactions.csv",
) -> pd.DataFrame:
    """
    Generate reproducible, realistic synthetic financial transaction dataset
    covering 12-18 months of history across multiple categories.
    """
    random.seed(seed)
    np.random.seed(seed)

    transactions: List[Dict[str, Any]] = []
    tx_counter = 1

    users = [
        {"user_id": 1, "base_salary": 5000.0, "rent": 1350.0, "spend_multiplier": 1.0},
        {"user_id": 2, "base_salary": 6500.0, "rent": 1800.0, "spend_multiplier": 1.2},
    ]

    # Generate records month by month for realistic financial lifecycle
    current_month_start = start_date

    for month_idx in range(num_months):
        year = current_month_start.year + (current_month_start.month + month_idx - 1) // 12
        month = (current_month_start.month + month_idx - 1) % 12 + 1

        # Determine days in this month
        if month == 12:
            days_in_month = 31
        else:
            days_in_month = (date(year, month + 1, 1) - date(year, month, 1)).days

        for user in users:
            uid = user["user_id"]
            mult = user["spend_multiplier"]

            # --- 1. INCOME ---
            # Monthly Salary (1st of month)
            salary_amt = round(user["base_salary"] + random.uniform(-50.0, 150.0), 2)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 1),
                "description": "Salary",
                "amount": salary_amt,
                "transaction_type": "income",
                "category": "Income",
            })
            tx_counter += 1

            # Occasional Freelance Income (~40% of months)
            if random.random() < 0.40:
                day = random.randint(10, 25)
                amt = round(random.uniform(400.0, 1200.0) * mult, 2)
                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, min(day, days_in_month)),
                    "description": "Freelance Income",
                    "amount": amt,
                    "transaction_type": "income",
                    "category": "Income",
                })
                tx_counter += 1

            # Quarterly / Bi-annual Bonus (every 6 months)
            if month in (6, 12) and random.random() < 0.85:
                day = random.randint(20, min(28, days_in_month))
                amt = round(random.uniform(1000.0, 2500.0) * mult, 2)
                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": "Bonus",
                    "amount": amt,
                    "transaction_type": "income",
                    "category": "Income",
                })
                tx_counter += 1

            # --- 2. HOUSING ---
            # Recurring Monthly Rent (2nd of month)
            rent_amt = round(user["rent"] + (50.0 if month_idx >= 12 else 0.0), 2)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 2),
                "description": "Rent",
                "amount": rent_amt,
                "transaction_type": "expense",
                "category": "Housing",
            })
            tx_counter += 1

            # Maintenance (Occasional, ~50% of months)
            if random.random() < 0.50:
                day = random.randint(5, 12)
                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": "Maintenance",
                    "amount": round(random.uniform(75.0, 150.0), 2),
                    "transaction_type": "expense",
                    "category": "Housing",
                })
                tx_counter += 1

            # --- 3. UTILITIES ---
            # Electricity (5th of month)
            elec_amt = round(random.uniform(70.0, 140.0) * (1.2 if month in (5, 6, 7, 12, 1) else 1.0), 2)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 5),
                "description": "Electricity",
                "amount": elec_amt,
                "transaction_type": "expense",
                "category": "Utilities",
            })
            tx_counter += 1

            # Water Bill (8th of month)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 8),
                "description": "Water Bill",
                "amount": round(random.uniform(30.0, 55.0), 2),
                "transaction_type": "expense",
                "category": "Utilities",
            })
            tx_counter += 1

            # Internet (10th of month)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 10),
                "description": "Internet",
                "amount": 69.99,
                "transaction_type": "expense",
                "category": "Utilities",
            })
            tx_counter += 1

            # Mobile Bill (12th of month)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 12),
                "description": "Mobile Bill",
                "amount": 45.00,
                "transaction_type": "expense",
                "category": "Utilities",
            })
            tx_counter += 1

            # --- 4. SUBSCRIPTIONS ---
            # Netflix (14th)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 14),
                "description": "Netflix",
                "amount": 15.99,
                "transaction_type": "expense",
                "category": "Subscription",
            })
            tx_counter += 1

            # Spotify (15th)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 15),
                "description": "Spotify",
                "amount": 10.99,
                "transaction_type": "expense",
                "category": "Subscription",
            })
            tx_counter += 1

            # Cloud Subscription (18th)
            transactions.append({
                "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                "user_id": uid,
                "date": date(year, month, 18),
                "description": "Cloud Subscription",
                "amount": 20.00,
                "transaction_type": "expense",
                "category": "Subscription",
            })
            tx_counter += 1

            # --- 5. FOOD (12 to 20 transactions per month) ---
            num_food = random.randint(14, 22)
            for _ in range(num_food):
                day = random.randint(1, days_in_month)
                food_type = random.choices(
                    ["Grocery Store", "Restaurant", "Food Delivery"],
                    weights=[0.45, 0.30, 0.25],
                )[0]
                if food_type == "Grocery Store":
                    amt = round(random.uniform(35.0, 160.0) * mult, 2)
                elif food_type == "Restaurant":
                    amt = round(random.uniform(25.0, 95.0) * mult, 2)
                else:
                    amt = round(random.uniform(15.0, 48.0) * mult, 2)

                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": food_type,
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Food",
                })
                tx_counter += 1

            # --- 6. TRANSPORT (8 to 15 transactions per month) ---
            num_transport = random.randint(8, 14)
            for _ in range(num_transport):
                day = random.randint(1, days_in_month)
                t_type = random.choices(
                    ["Fuel", "Metro", "Cab", "Bus"],
                    weights=[0.40, 0.25, 0.20, 0.15],
                )[0]
                if t_type == "Fuel":
                    amt = round(random.uniform(35.0, 70.0), 2)
                elif t_type == "Cab":
                    amt = round(random.uniform(12.0, 38.0), 2)
                elif t_type == "Metro":
                    amt = round(random.uniform(3.0, 7.5), 2)
                else:
                    amt = round(random.uniform(2.0, 5.0), 2)

                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": t_type,
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Transport",
                })
                tx_counter += 1

            # --- 7. SHOPPING (2 to 4 transactions per month) ---
            num_shopping = random.randint(2, 4)
            for _ in range(num_shopping):
                day = random.randint(1, days_in_month)
                s_type = random.choices(
                    ["Clothing", "Electronics", "Household Shopping"],
                    weights=[0.40, 0.20, 0.40],
                )[0]
                if s_type == "Electronics":
                    amt = round(random.uniform(60.0, 350.0) * mult, 2)
                elif s_type == "Clothing":
                    amt = round(random.uniform(40.0, 180.0) * mult, 2)
                else:
                    amt = round(random.uniform(25.0, 110.0) * mult, 2)

                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": s_type,
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Shopping",
                })
                tx_counter += 1

            # --- 8. ENTERTAINMENT (2 to 4 transactions per month) ---
            num_ent = random.randint(2, 4)
            for _ in range(num_ent):
                day = random.randint(1, days_in_month)
                e_type = random.choices(["Movies", "Events", "Games"], weights=[0.45, 0.25, 0.30])[0]
                if e_type == "Movies":
                    amt = round(random.uniform(15.0, 38.0), 2)
                elif e_type == "Events":
                    amt = round(random.uniform(45.0, 130.0) * mult, 2)
                else:
                    amt = round(random.uniform(19.99, 69.99), 2)

                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": e_type,
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Entertainment",
                })
                tx_counter += 1

            # --- 9. HEALTHCARE (1 to 2 transactions per month) ---
            if random.random() < 0.70:
                day = random.randint(1, days_in_month)
                h_type = random.choices(["Pharmacy", "Doctor", "Medical"], weights=[0.60, 0.25, 0.15])[0]
                if h_type == "Doctor":
                    amt = round(random.uniform(70.0, 150.0), 2)
                elif h_type == "Medical":
                    amt = round(random.uniform(40.0, 120.0), 2)
                else:
                    amt = round(random.uniform(15.0, 55.0), 2)

                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": h_type,
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Healthcare",
                })
                tx_counter += 1

            # --- 10. OTHER (1 to 2 transactions per month) ---
            if random.random() < 0.60:
                day = random.randint(1, days_in_month)
                amt = round(random.uniform(12.0, 75.0), 2)
                transactions.append({
                    "transaction_id": f"TXN-{year}{month:02d}-{tx_counter:05d}",
                    "user_id": uid,
                    "date": date(year, month, day),
                    "description": "Miscellaneous",
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Other",
                })
                tx_counter += 1

    df = pd.DataFrame(transactions)
    # Sort chronologically by date and transaction_id
    df = df.sort_values(by=["date", "transaction_id"]).reset_index(drop=True)

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    print(f"Generated {len(df)} transactions across {num_months} months to {dest}")
    return df


if __name__ == "__main__":
    generate_transactions()
