import sys
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

# Add backend directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal, create_tables, engine
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from ml.budget_analysis import generate_sample_budgets


def load_sample_data(
    transactions_csv: str = "data/processed/cleaned_transactions.csv"
):
    print("=" * 60)
    print("FinPilot PostgreSQL Sample Data Loader")
    print(f"Target Database: {engine.url}")
    print("=" * 60)

    # 1. Ensure database tables exist
    create_tables()

    csv_path = Path(transactions_csv)
    if not csv_path.exists():
        fallback_path = Path("data/sample/transactions.csv")
        if fallback_path.exists():
            csv_path = fallback_path
        else:
            print(f"Error: Neither {csv_path} nor {fallback_path} exists. Run pipeline first.")
            sys.exit(1)

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    print(f"Loaded {len(df)} records from {csv_path}")

    db = SessionLocal()
    try:
        # 2. Ensure Users exist
        users_info = {
            1: {"name": "Alex Miller", "email": "alex.miller@finpilot.ai"},
            2: {"name": "Sophia Chen", "email": "sophia.chen@finpilot.ai"},
        }

        unique_uids = df["user_id"].unique()
        for uid in unique_uids:
            uid_int = int(uid)
            info = users_info.get(uid_int, {"name": f"User {uid_int}", "email": f"user{uid_int}@finpilot.ai"})
            user = db.query(User).filter(User.id == uid_int).first()
            if not user:
                user = User(id=uid_int, name=info["name"], email=info["email"])
                db.add(user)
        db.commit()

        # 3. Load Transactions (Idempotent / No Duplicates)
        incoming_ids = set(df["transaction_id"].astype(str))
        existing_tx_ids = set(
            tx_id for (tx_id,) in db.query(Transaction.transaction_id)
            .filter(Transaction.transaction_id.in_(incoming_ids))
            .all()
        )

        new_tx_records = []
        for _, row in df.iterrows():
            tx_id = str(row["transaction_id"])
            if tx_id in existing_tx_ids:
                continue

            new_tx_records.append(
                Transaction(
                    transaction_id=tx_id,
                    user_id=int(row["user_id"]),
                    date=row["date"],
                    description=str(row["description"]),
                    amount=float(row["amount"]),
                    transaction_type=str(row["transaction_type"]).lower(),
                    category=str(row["category"]),
                )
            )

        if new_tx_records:
            db.bulk_save_objects(new_tx_records)
            db.commit()

        total_tx_in_db = db.query(Transaction).count()
        print(f"Transactions: {len(new_tx_records)} newly inserted, {len(existing_tx_ids)} skipped (duplicates). Total in DB: {total_tx_in_db}")

        # 4. Generate and Load Budget Records
        budgets_df = generate_sample_budgets(df)
        existing_budgets = set(
            (b.user_id, b.category, b.month)
            for b in db.query(Budget.user_id, Budget.category, Budget.month).all()
        )

        new_budget_records = []
        for _, brow in budgets_df.iterrows():
            key = (int(brow["user_id"]), str(brow["category"]), str(brow["month"]))
            if key in existing_budgets:
                continue

            new_budget_records.append(
                Budget(
                    user_id=key[0],
                    category=key[1],
                    month=key[2],
                    budget_amount=float(brow["budget_amount"]),
                )
            )

        if new_budget_records:
            db.bulk_save_objects(new_budget_records)
            db.commit()

        total_budgets_in_db = db.query(Budget).count()
        print(f"Budgets:      {len(new_budget_records)} newly inserted, {len(existing_budgets)} skipped. Total in DB: {total_budgets_in_db}")

        print("\nVerification:")
        users_count = db.query(User).count()
        print(f"  - Verified Users in DB:        {users_count}")
        print(f"  - Verified Transactions in DB: {total_tx_in_db}")
        print(f"  - Verified Budgets in DB:      {total_budgets_in_db}")

    except Exception as e:
        db.rollback()
        print(f"Error loading data into PostgreSQL: {e}")
        raise
    finally:
        db.close()

    print("=" * 60)
    print("DATA LOAD COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    load_sample_data()
