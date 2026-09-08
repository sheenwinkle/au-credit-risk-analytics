# Australian Credit Risk Analytics

Credit risk modelling and portfolio analytics project built for Australian banking, FinTech, risk analyst, credit risk, and model risk roles.

The project estimates applicant probability of default, chooses a cost-sensitive credit decision threshold, validates rank ordering and calibration, produces a score-band monitoring table, and includes PostgreSQL-ready SQL assets for risk reporting.

## Business Problem

Australian lenders need to approve profitable borrowers while meeting responsible lending expectations and controlling arrears/default losses. This project frames a practical retail credit workflow:

1. Ingest credit application data from a legally usable public source or an offline demo sample.
2. Clean mixed numeric/categorical application attributes.
3. Train an interpretable baseline and a stronger challenger model.
4. Select a threshold that treats approved bad accounts as more costly than declined good accounts.
5. Validate discrimination, calibration, bad-rate lift, approval rate, and score-band stability.
6. Export scored applications and SQL-ready reporting tables.

## Data

Default data source: OpenML `credit-g` dataset, `data_id=31`, originally from UCI Statlog German Credit.

- OpenML dataset: <https://www.openml.org/d/31>
- UCI dataset page: <https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data>
- UCI license: CC BY 4.0

The repo does not commit raw third-party data. Running the pipeline downloads the public data into `data/raw/`. If OpenML is unavailable, the code falls back to a deterministic synthetic credit application dataset so the project remains runnable in interviews or offline demos.

## Project Structure

```text
.
├── data/
│   ├── raw/                 # Downloaded or generated raw data, gitignored
│   ├── processed/           # Processed data, scores, local SQLite demo, gitignored
│   └── sample/              # Small generated sample, safe for demo use
├── docs/
│   └── model_card.md        # Model risk and validation notes
├── models/                  # Trained model artifact, gitignored
├── reports/
│   ├── figures/             # EDA and model validation charts, gitignored
│   ├── gains_table.csv
│   ├── metrics.json
│   └── permutation_importance.csv
├── sql/
│   ├── 01_postgres_schema.sql
│   ├── 02_monitoring_views.sql
│   └── 03_analysis_queries.sql
├── src/credit_risk_au/
│   ├── data.py
│   ├── features.py
│   ├── modeling.py
│   ├── evaluate.py
│   ├── explain.py
│   ├── database.py
│   └── train.py
└── tests/
```

## Method

Baseline model:

- Balanced logistic regression.
- Used for transparent odds-ratio style feature effects.

Main model:

- Sigmoid-calibrated gradient boosting classifier.
- Handles non-linear relationships and interactions across loan term, amount, history, arrears, and affordability-like features.

Validation:

- ROC AUC and Gini for discriminatory power.
- KS statistic for rank separation.
- Average precision for bad-account retrieval.
- Brier score, calibration intercept/slope, expected calibration error, and calibration plot.
- Cost-sensitive threshold where false negatives, bad borrowers approved, cost more than false positives.
- Gains table by risk decile for risk policy and portfolio monitoring.
- Permutation importance for model explainability.
- Five-fold out-of-fold model selection on the development sample.
- Locked 20% test sample used only after the champion and threshold are frozen.
- Bootstrap 95% confidence intervals to show sampling uncertainty.

## Latest Reproducible Results

The checked pipeline was run on the OpenML/UCI dataset with an 80/20 development/test split. Model and cutoff selection use five-fold out-of-fold predictions within the development sample; the test sample remains locked until selection is complete.

| Model | OOF AUC | OOF Cost / App | Locked-test AUC | Test Brier | Test Cost / App |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic baseline | 0.770 | 0.524 | 0.804 | 0.155 | 0.575 |
| Calibrated gradient boosting | **0.789** | **0.499** | 0.793 | 0.160 | 0.580 |

Calibrated gradient boosting is selected before test evaluation because it has stronger out-of-fold AUC and lower out-of-fold cost. On the locked test sample its AUC is 0.793 (95% bootstrap CI 0.718-0.860) and its cost per application is 0.580 (95% CI 0.445-0.735). The logistic model happens to score slightly better on the test sample, but the champion is not changed after observing test results. This is a deliberate model-risk control rather than a post-hoc choice of the most favourable number.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m credit_risk_au.train --source openml
pytest
```

Offline/demo mode:

```bash
python -m credit_risk_au.train --source sample
```

The main command writes:

- `reports/metrics.json`
- `reports/gains_table.csv`
- `reports/permutation_importance.csv`
- `reports/baseline_logistic_effects.csv`
- `reports/model_comparison.csv`
- `reports/threshold_strategy.csv`
- `reports/bootstrap_intervals.json`
- `reports/figures/*.png`
- `models/credit_risk_model.joblib`
- `data/processed/scored_test_applications.csv`
- `data/processed/credit_risk_demo.sqlite`

## Example Local SQLite Check

The training run builds a small local database mirror for reviewers who do not have PostgreSQL running.

```bash
python -m credit_risk_au.train --source sample
python - <<'PY'
import sqlite3
conn = sqlite3.connect("data/processed/credit_risk_demo.sqlite")
for row in conn.execute("SELECT * FROM score_monitoring_summary LIMIT 5"):
    print(row)
PY
```

For a PostgreSQL deployment, run the scripts in `sql/` in order, then load application and score outputs into the matching tables.

## Portfolio Relevance

This project is designed to show:

- Python ML workflow with clean package structure.
- Credit risk concepts: PD, bad rate, approval rate, cutoff selection, score deciles, Gini, KS, calibration.
- Model risk mindset: out-of-fold baseline/challenger selection, locked test policy, calibration, bootstrap uncertainty, interpretability, threshold assumptions, and limitations.
- SQL capability through schema design, monitoring views, and reusable analysis queries.
- Public GitHub readiness: no private data, reproducible commands, tests, and clear artifacts.

## Resume Bullets

- Built an end-to-end credit risk analytics project in Python, selecting a calibrated gradient-boosting champion using five-fold out-of-fold validation and evaluating it once on a locked test set (AUC 0.793; 95% bootstrap CI 0.718-0.860).
- Designed PostgreSQL-ready credit risk tables and monitoring views for scored applications, approval rate tracking, and model validation reporting.
- Implemented reproducible data ingestion, feature preprocessing, cost-sensitive thresholding, model explainability, automated tests, and public GitHub documentation for banking/FinTech risk analyst roles.

## Next Steps

- Add an Australian macroeconomic overlay and monthly account-performance portfolio.
- Add vintage, roll-rate, expected-loss, and population-stability monitoring.
- Add a Streamlit dashboard for score-band monitoring and manual underwriting review.
- Add reject inference and adverse-action reason-code analysis.
- Replace the demo dataset with an Australian lender-approved internal dataset if used in a private workplace setting.
