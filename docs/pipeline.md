# FinPilot End-to-End Financial Intelligence Pipeline

This document details the complete 12-stage architecture, data flow, validation gates, mathematical foundations, and Responsible-AI safeguards of the **FinPilot AI/ML Intelligence Layer**.

---

## Architecture Flow

```
[ Financial Data Input / Raw CSV ]
                │
                ▼
[ 1. Data Cleaning & Validation ]
                │  ├─ Schema verification & ISO date validation
                │  ├─ Positive amount enforcement & duplicate deduplication
                │  └─ Rejection audit logging
                ▼
[ 2. Expense Categorization ]
                │  ├─ Transparent keyword & pattern matching
                │  └─ Granular audit trail for matched rules
                ▼
[ 3. Feature Engineering ]
                │  ├─ Monthly income, expense, net cash flow & savings rate
                │  ├─ Daily spending volatility (standard deviation)
                │  └─ Essential vs. Discretionary vs. Recurring aggregation
                ▼
[ 4. Financial Behavior Analysis ]
                │  ├─ Dynamic threshold evaluations
                │  └─ Structured health indicators & trend assessments
                ▼
[ 5. Budget Tracking & Variance ]
                │  ├─ Category & monthly limit reconciliation
                │  └─ Variance calculation & overspending flags
                ▼
[ 6. Expense Forecasting ]
                │  ├─ Ridge regression with time-index & cyclical seasonality
                │  ├─ 3-month historical rolling window
                │  ├─ Prediction intervals (95% CI)
                │  └─ Category-level decomposition
                ▼
[ 7. Forecast Evaluation ]
                │  ├─ Strict chronological train/test split (no lookahead leakage)
                │  └─ MAE, RMSE, and zero-safe MAPE metrics
                ▼
[ 8. Budget Recommendations ]
                │  ├─ Dynamic rules triggered by actual user metrics
                │  └─ Structured evidence, priorities, confidence & assumptions
                ▼
[ 9. Investment Decision Support ]
                │  ├─ Non-autonomous educational decision support
                │  ├─ Emergency fund readiness & cash-flow stability check
                │  └─ Explicit disclaimers (no return guarantees or trade execution)
                ▼
[ 10. Wealth Optimization ]
                │  ├─ Scenario modeling (Baseline, Moderate, Aggressive, Recurring Trim)
                │  ├─ Horizon projections (6m, 12m, 24m, 36m)
                │  └─ Comparative surplus & savings improvement metrics
                ▼
[ 11. Explainable Financial Insights ]
                │  ├─ Transparent feature attribution & historical baselines
                │  └─ Scenario change explanations & confidence bounds
                ▼
[ 12. Responsible AI Guardrails ]
                   ├─ Data sufficiency verification
                   ├─ Input sanitization & bounds clamping
                   └─ Mandatory regulatory & risk disclaimers
```

---

## 1. Data Cleaning & Validation
* **Ingestion**: Raw transaction streams ingested via filesystem (`data/sample/transactions.csv`) or multipart REST upload (`POST /api/transactions/upload`).
* **Validation Gates**:
  * Mandatory fields checked: `transaction_id`, `user_id`, `date`, `description`, `amount`, `transaction_type`, `category`.
  * Dates must parse to standard calendar dates; amounts must be strictly positive numeric values (`> 0.0`).
  * `transaction_type` must be strictly `income` or `expense`.
  * Duplicate `transaction_id` entries are detected and rejected.
* **Audit Trail**: Rejected records are preserved in diagnostic tables with specific failure reasons rather than silently dropped. Clean records are formatted and ordered chronologically in `data/processed/cleaned_transactions.csv`.

## 2. Expense Categorization
* Implements extensible `BaseCategorizer` interface.
* Employs `RuleBasedCategorizer` with regex keyword matching across 10 financial categories:
  * **Income**: `salary`, `freelance`, `bonus`, `dividend`, `interest`
  * **Housing**: `rent`, `mortgage`, `maintenance`, `hoa`
  * **Food**: `grocery`, `supermarket`, `restaurant`, `cafe`, `dining`
  * **Transport**: `fuel`, `metro`, `cab`, `bus`, `uber`, `gas`
  * **Utilities**: `electricity`, `water bill`, `internet`, `mobile bill`
  * **Subscription**: `netflix`, `spotify`, `prime`, `cloud subscription`
  * **Entertainment**: `movies`, `events`, `games`, `theater`
  * **Healthcare**: `pharmacy`, `doctor`, `medical`, `clinic`
  * **Shopping**: `clothing`, `electronics`, `retail`
  * **Other**: Fallback for unclassified expenditures
* Every record retains an explicit `category_rule` audit trace explaining categorization logic.

## 3. Feature Engineering
* Aggregates transactions into monthly cohorts by `user_id` and `month` (`YYYY-MM`).
* Mathematical formulas:
  $$\text{Net Cash Flow} = \text{Monthly Income} - \text{Monthly Expenses}$$
  $$\text{Savings Rate (\%)} = \begin{cases} \frac{\text{Net Cash Flow}}{\text{Monthly Income}} \times 100, & \text{if Income} > 0 \\ 0.0, & \text{if Income} \le 0 \end{cases}$$
* Computes daily expense volatility ($\sigma_{\text{daily}}$), discretionary spending ratio, essential spending ratio, recurring commitments, and category concentration indices.
* Output is stored in `data/processed/monthly_features.csv`.

## 4. Financial Behavior Analysis
* Evaluates financial health against configurable thresholds (`BehaviorThresholds`).
* Generates structured indicator diagnostics:
  * Savings rate adequacy (target $\ge 20\%$)
  * Expense-to-income ratio (caution $> 80\%$, critical $> 100\%$)
  * Spending stability index via coefficient of variation
  * Month-over-month spending growth acceleration ($\Delta > 15\%$)
  * Recurring spending commitment ratio (caution $> 50\%$)

## 5. Budget Tracking & Variance Analysis
* Compares actual spending against allocated category limits:
  $$\text{Variance} = \text{Actual Spending} - \text{Budget Amount}$$
  $$\text{Remaining Budget} = \text{Budget Amount} - \text{Actual Spending}$$
  $$\text{Utilization (\%)} = \frac{\text{Actual Spending}}{\text{Budget Amount}} \times 100$$
* Triggers real-time status alerts: `within_budget` ($< 85\%$), `warning` ($85\% - 100\%$), and `over_budget` ($> 100\%$).

---

## 6. Expense Forecasting Pipeline

### Methodology & Model Selection
* **Model**: L2-regularized Ridge Regression (`sklearn.linear_model.Ridge(alpha=1.0)`).
* **Rationale**: Given typical personal finance datasets (12–36 monthly observations), complex neural architectures or high-capacity regressors suffer from severe overfitting. Ridge regression provides stable coefficients, handles collinear features gracefully, and produces explainable linear weights.
* **Engineered Time-Series Features**:
  1. `t`: Normalized linear time index representing long-term trend.
  2. `month_sin`, `month_cos`: Fourier cyclical transformation of calendar month:
     $$\text{month\_sin} = \sin\left(\frac{2\pi \cdot m}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot m}{12}\right)$$
  3. `lag_1`: Expense total of previous month ($t-1$).
  4. `rolling_mean_3`: 3-month trailing moving average.
* **Category-Level Decomposition**: Historical category proportions (weighted by recency) are modeled alongside total expenses to project forward category-by-category allocations.
* **Uncertainty Quantification**: Calculates empirical residual standard deviation $\sigma_{\text{res}}$ from training fits to generate 95% confidence intervals:
  $$\hat{y}_t \pm 1.96 \cdot \sigma_{\text{res}} \cdot \sqrt{1 + \frac{h-1}{6}}$$
  where $h$ is the prediction horizon step.

---

## 7. Forecast Evaluation

### Chronological Holdout Validation
* **Zero Lookahead Leakage**: Standard random train/test splits are strictly prohibited for time-series.
* **Chronological Split**: For a dataset of $N$ monthly observations (minimum 6 months required):
  * **Training Set**: Chronological months $1$ to $N - 3$ (e.g., 2025-01 through 2026-03, 15 months).
  * **Evaluation Holdout**: Final 3 contiguous months (e.g., 2026-04 through 2026-06).
* **Evaluation Metrics**:
  * **MAE (Mean Absolute Error)**:
    $$\text{MAE} = \frac{1}{K} \sum_{k=1}^K |y_k - \hat{y}_k|$$
  * **RMSE (Root Mean Squared Error)**:
    $$\text{RMSE} = \sqrt{\frac{1}{K} \sum_{k=1}^K (y_k - \hat{y}_k)^2}$$
  * **MAPE (Mean Absolute Percentage Error)**:
    $$\text{MAPE} = \frac{100\%}{K} \sum_{k=1}^K \left|\frac{y_k - \hat{y}_k}{y_k}\right| \quad (\text{guarded against } y_k = 0)$$

### Verified Benchmark Performance (18-Month Synthetic Dataset)
* **Training Window**: 15 months (`2025-01` to `2026-03`)
* **Evaluation Window**: 3 months (`2026-04` to `2026-06`)
* **MAE**: **$223.68**
* **RMSE**: **$247.11**
* **MAPE**: **6.20%**
* Results artifact saved at `models/forecast_evaluation.json`.

---

## 8. Personalized Budget Recommendations

### Dynamic Rule Engine
Recommendations are derived dynamically from actual computed financial metrics; no static strings are hardcoded.

1. **Top Spending Driver Detection**:
   * *Trigger*: Highest spending category exceeds 30% of total expenses.
   * *Action*: Targets driver with spending mitigation advice.
2. **Persistent Budget Overspending**:
   * *Trigger*: Overall spending exceeds allocated budget, or specific categories consistently breach caps.
   * *Action*: Recommends specific dollar cap adjustments.
3. **Savings Rate Pressure**:
   * *Trigger*: Current savings rate $< 15\%$, or trailing 3-month savings rate shows negative slope.
   * *Action*: Prioritizes cash-flow preservation and spending audits.
4. **Discretionary Spending Imbalance**:
   * *Trigger*: Discretionary expenses exceed 35% of total income.
   * *Action*: Recommends trimming non-essential expenditures (dining, entertainment, shopping).
5. **High Recurring Commitment Burden**:
   * *Trigger*: Fixed/recurring costs exceed 50% of monthly income.
   * *Action*: Advises subscription consolidation and utility tariff renegotiations.
6. **Positive Cash-Flow Surplus Optimization**:
   * *Trigger*: Positive net cash flow with savings rate $\ge 20\%$.
   * *Action*: Recommends strategic allocation of monthly surplus towards long-term objectives.

### Required Output Contract
Each recommendation includes: `recommendation`, `reason`, `evidence` (actual numeric values), `priority` (`HIGH`, `MEDIUM`, `LOW`), `confidence` (0.0–1.0), `assumptions`, and `limitations`.

---

## 9. Investment Decision Support

### Educational Non-Autonomous Architecture
FinPilot strictly serves as a **decision-support tool**. It does not:
* Connect to brokerages or execute financial transactions.
* Guarantee returns or promise capital appreciation.
* Recommend speculative individual equities or derivative contracts.

### Decision Rules Grounded in User Financial Readiness
1. **Emergency Reserve Readiness**:
   * Calculates monthly essential expenses (Housing + Utilities + Food + Healthcare + Transport).
   * Verifies if liquid savings support a 3-to-6 month emergency runway before considering investment options.
2. **Cash Flow & Stability Check**:
   * Evaluates trailing cash-flow volatility. If net cash flow is negative or erratic, investments are deferred in favor of liquidity stabilization.
3. **Risk Profile Alignment**:
   * Incorporates user risk preference (`conservative`, `moderate`, `aggressive`) alongside time horizon to suggest diversified asset allocation concepts (e.g., broad-market index funds, high-yield liquid instruments).
4. **Insufficient Data Gate**:
   * If historical records are fewer than 3 months, system explicitly returns:
     `"Insufficient financial information for investment-oriented recommendation."`

---

## 10. Wealth Optimization Analysis

### Scenario Modeling Engine
Simulates realistic cash-flow adjustments across multi-period planning horizons (6, 12, 24, and 36 months):
* **Baseline**: Current empirical income and spending trajectory without behavioral modifications.
* **Moderate Discretionary Optimization**: Trims 15% from flexible discretionary categories (shopping, dining, entertainment).
* **Aggressive Discretionary Optimization**: Trims 30% from flexible discretionary categories.
* **Recurring Expense Optimization**: Trims 10% from recurring commitments (subscriptions, utilities).
* **Balanced Optimization**: Combines 15% discretionary trimming with 10% recurring optimization.

### Projection Formula
$$\text{Projected Total Savings} = \text{Monthly Surplus}_{\text{scenario}} \times \left[ \frac{(1 + r/12)^H - 1}{r/12} \right]$$
where $H$ is the planning horizon in months, and $r$ is an explicitly labeled conservative nominal return assumption (default $4.0\%$ p.a.).

### Outputs
Returns: `baseline_scenario`, `scenarios` (sorted by cumulative financial improvement), `key_changes`, `projected_savings_difference`, `assumptions`, and `limitations`.

---

## 11. Explainable Financial Insights

Every intelligence output is accompanied by transparent, audit-ready explanations:
* **Forecast Insights**: Displays historical spending baseline ($3-month moving average), dominant spending category contributors, identified trend direction (slope), model evaluation metrics (MAE, RMSE, MAPE), and residual uncertainty bounds.
* **Recommendation Insights**: Lists triggering financial ratios, comparative benchmark disparities, quantitative evidence, and underlying behavioral assumptions.
* **Optimization Insights**: Details line-item dollar modifications per category, projected monthly cash-flow deltas, and multi-year cumulative gains.

---

## 12. Responsible AI Safeguards

Implemented via `backend/ml/responsible_ai.py` to prevent hallucination, unwarranted certainty, or hazardous financial guidance:
1. **Zero Data Fabrication**: Never fabricates transaction records, historical balances, income, or investment returns.
2. **Strict Non-Autonomous Boundary**: Never attempts trade execution or account alteration.
3. **Data Sufficiency Gating**: Minimum data thresholds enforced (3 months for basic recommendations, 6 months for time-series forecasting). Insufficient data triggers informative informational notices.
4. **Input Sanitization**: User planning inputs are validated and clamped to realistic ranges (savings adjustments restricted between $0\%$ and $50\%$, time horizons between 1 and 360 months).
5. **Universal Disclaimers**: All outputs explicitly state educational decision-support status and advise consulting licensed financial professionals.
