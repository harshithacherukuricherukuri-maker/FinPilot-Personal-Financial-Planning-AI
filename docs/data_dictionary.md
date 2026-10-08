# FinPilot Data Dictionary

This document details the core transaction schema, database entities, and engineered monthly financial features for the FinPilot platform.

---

## 1. Raw & Processed Transaction Schema

| Column | Type | Nullable | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | String / VARCHAR(100) | No | Unique identifier for each transaction (traceable across all pipeline stages) | `TXN-202501-00001` |
| `user_id` | Integer | No | Foreign key linking to the `users` table | `1` |
| `date` | Date | No | Transaction posting date (`YYYY-MM-DD`) | `2025-01-02` |
| `description` | String / VARCHAR(255) | No | Normalized text description of the merchant, service, or event | `Grocery Store`, `Rent`, `Salary` |
| `amount` | Float / Numeric(12,2) | No | Transaction value in currency units (strictly positive `> 0.0`) | `125.50` |
| `transaction_type`| String / VARCHAR(50) | No | Direction of funds: `income` or `expense` | `expense` |
| `category` | String / VARCHAR(100) | No | Financial classification of the transaction | `Food`, `Housing`, `Utilities` |
| `categorization_rule` | String (pipeline only) | Yes | Diagnostic audit rule explaining categorization | `Matched 'grocery' via rule_food_keyword` |

---

## 2. Database Entities

### `users`
* `id` (INTEGER, PK): Unique user identifier.
* `name` (VARCHAR): User's full name.
* `email` (VARCHAR, Unique): Primary email address.
* `created_at` (TIMESTAMP WITH TIME ZONE): Account registration timestamp.

### `transactions`
* `id` (INTEGER, PK): Primary database auto-increment ID.
* `transaction_id` (VARCHAR(100), Unique, Indexed): Business unique transaction ID.
* `user_id` (INTEGER, FK -> `users.id`, Indexed): Associated user.
* `date` (DATE, Indexed): Transaction date.
* `description` (VARCHAR(255)): Merchant/item description.
* `amount` (FLOAT): Transaction amount.
* `transaction_type` (VARCHAR(50)): `income` or `expense`.
* `category` (VARCHAR(100), Indexed): Categorization label.
* `created_at` (TIMESTAMP WITH TIME ZONE): Database insertion timestamp.

### `budgets`
* `id` (INTEGER, PK): Primary database auto-increment ID.
* `user_id` (INTEGER, FK -> `users.id`, Indexed): Associated user.
* `category` (VARCHAR(100), Indexed): Target spending category.
* `month` (VARCHAR(7), Indexed): Target calendar month (`YYYY-MM`).
* `budget_amount` (FLOAT): Allocated budget allowance.
* `created_at` (TIMESTAMP WITH TIME ZONE): Record creation timestamp.

---

## 3. Engineered Monthly Features (`data/processed/monthly_features.csv`)

| Feature Column | Type | Formula / Definition | Purpose |
| :--- | :--- | :--- | :--- |
| `user_id` | Integer | User identifier | Grouping and segmentation |
| `month` | String | Calendar month in `YYYY-MM` format | Time-series aggregation |
| `monthly_income` | Float | $\sum \text{amount}_{\text{income}}$ in month | Total inflow |
| `monthly_expenses`| Float | $\sum \text{amount}_{\text{expense}}$ in month | Total outflow |
| `monthly_net_cash_flow` | Float | $\text{Income} - \text{Expenses}$ | Monthly savings/surplus |
| `savings_rate` | Float | $\frac{\text{Net Cash Flow}}{\text{Income}} \times 100$ (0 if income = 0) | Percentage of income saved |
| `transaction_frequency` | Integer | Total count of transactions in month | Financial activity volume |
| `expense_transaction_count` | Integer | Total count of expense transactions | Outflow activity volume |
| `average_transaction_amount` | Float | $\text{Mean}(\text{expense amounts})$ | Average expenditure ticket size |
| `spending_volatility` | Float | $\text{StdDev}(\text{daily expense totals})$ | Measure of daily spending variability |
| `recurring_spending` | Float | Sum of expenses in Housing, Utilities, Subscriptions | Committed fixed overhead |
| `essential_spending` | Float | Sum of expenses in Housing, Utilities, Food, Healthcare, Transport | Needs-based non-negotiable spend |
| `discretionary_spending`| Float | Sum of expenses in Shopping, Entertainment, Subscriptions, Other | Lifestyle and discretionary spend |
| `category_concentration`| Float | $\frac{\max(\text{Category Spend})}{\text{Total Expenses}} \times 100$ | Dependence on single category (%) |
| `top_category` | String | Category with highest expense in month | Dominant spending driver |
| `spend_<category>` | Float | Total expense for `<category>` in month | Individual category totals |
