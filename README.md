# Australian Credit Risk Analytics

[![quality](https://github.com/sheenwinkle/au-credit-risk-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/sheenwinkle/au-credit-risk-analytics/actions/workflows/ci.yml)

Credit risk modelling and portfolio analytics project built for Australian banking, FinTech, risk analyst, credit risk, and model risk roles.

The project estimates applicant probability of default, chooses a cost-sensitive credit decision threshold, validates rank ordering and calibration, produces score-band monitoring, builds a monthly account-performance mart, adds IFRS 9-style expected-credit-loss provisioning analytics, and includes reject-inference and challenger-monitoring controls with PostgreSQL-ready reporting assets.

The project is structured as an APRA-style public portfolio demonstrator: it uses prudential risk-management habits around scope, evidence, controls, thresholds, limitations, and escalation, without claiming APRA compliance, production readiness, or real lending suitability. See [`docs/apra_style_framework.md`](docs/apra_style_framework.md).

## Business Problem

Australian lenders need to approve profitable borrowers while meeting responsible lending expectations and controlling arrears/default losses. This project frames a practical retail credit workflow:

1. Ingest credit application data from a legally usable public source or an offline demo sample.
2. Clean mixed numeric/categorical application attributes.
3. Train an interpretable baseline and a stronger challenger model.
4. Select a threshold that treats approved bad accounts as more costly than declined good accounts.
5. Validate discrimination, calibration, bad-rate lift, approval rate, and score-band stability.
6. Monitor monthly arrears, roll rates, vintage defaults, stress expected loss, and Stage 1/2/3 provision coverage.
7. Analyse reject-inference sensitivity and challenger-model alerts without making post-hoc champion changes.
8. Export scored applications, portfolio analytics, monitoring alerts, and SQL-ready reporting tables.

## Data

Default data source: OpenML `credit-g` dataset, `data_id=31`, originally from UCI Statlog German Credit.

- OpenML dataset: <https://www.openml.org/d/31>
- UCI dataset page: <https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data>
- UCI license: CC BY 4.0

The repo does not commit raw third-party data. Running the pipeline downloads the public data into `data/raw/`. If OpenML is unavailable, the code falls back to a deterministic synthetic credit application dataset so the project remains runnable in interviews or offline demos.

The portfolio workflow separately downloads four public RBA/ABS macro series and joins them to a deterministic synthetic Australian account-performance panel. This expands the analytical data from 1,000 application rows to thousands of accounts and tens of thousands of monthly observations without presenting synthetic customer records as real lender data. See [`docs/data_sources.md`](docs/data_sources.md) for licensing and attribution.

Latest generated portfolio profile:

- 3,000 Australian-labelled synthetic retail credit accounts.
- 105,520 account-month performance records across 60 reporting months.
- 231 simulated defaults with balances, write-offs, recoveries, PD, LGD, EAD, and expected loss.
- 318 months of official macro history available for scenario joins.
- IFRS 9-style Stage 1/2/3 provision outputs at account, product, risk-band, and monthly levels.

## Project Structure

```text
.
├── .vscode/                # Local tasks, debugger, tests, and extension recommendations
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
├── tests/
└── compose.yaml            # One-command local container deployment
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
- IFRS 9-style ECL staging using DPD, default status, PD uplift, lifetime PD, LGD, and EAD.
- Reject-inference sensitivity comparing approved-only observed risk, PD parceling, and hidden-label backtesting on the public demonstration sample.
- Challenger monitoring alerts for locked-test rank-order instability, calibration review, and challenger AUC/Brier/cost outperformance.

## Latest Reproducible Results

The checked pipeline was run on the OpenML/UCI dataset with an 80/20 development/test split. Model and cutoff selection use five-fold out-of-fold predictions within the development sample; the test sample remains locked until selection is complete.

| Model | OOF AUC | OOF Cost / App | Locked-test AUC | Test Brier | Test Cost / App |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic baseline | 0.770 | 0.524 | 0.804 | 0.155 | 0.575 |
| Calibrated gradient boosting | **0.789** | **0.499** | 0.793 | 0.160 | 0.580 |

Calibrated gradient boosting is selected before test evaluation because it has stronger out-of-fold AUC and lower out-of-fold cost. On the locked test sample its AUC is 0.793 (95% bootstrap CI 0.718-0.860) and its cost per application is 0.580 (95% CI 0.445-0.735). The logistic model happens to score slightly better on the test sample, but the champion is not changed after observing test results. This is a deliberate model-risk control rather than a post-hoc choice of the most favourable number.

## Portfolio Monitoring Results

The latest deterministic portfolio run produces:

| Measure | Result |
| --- | ---: |
| Accounts | 3,000 |
| Account-month records | 105,520 |
| Latest exposure | AUD 7.49m |
| 30+ DPD balance rate | 2.87% |
| 90+ DPD balance rate | 1.72% |
| Simulated defaults | 231 |
| Base expected loss | AUD 232.8k |
| Severe expected loss | AUD 520.7k |
| Severe vs base increase | 123.6% |
| Population Stability Index | 2.404 |
| IFRS 9-style ECL provision | AUD 291.8k |
| Stage 2/3 exposure | AUD 214.6k |
| Stage 3 coverage ratio | 48.7% |
| Approved-only bad rate | 11.1% |
| PD-parcelled through-the-door bad rate | 30.8% |
| Hidden through-the-door bad rate | 30.0% |
| Open model monitoring alerts | 5 |

The high PSI is treated as a monitoring alert caused by macro-sensitive PD movement and portfolio composition change, not as a positive model-performance result. See [`docs/portfolio_methodology.md`](docs/portfolio_methodology.md) for definitions and limitations.

The IFRS 9 layer is a transparent analytical approximation for portfolio demonstration. It is not a statutory impairment model, but it shows how PD, LGD, EAD, arrears, and significant risk deterioration can flow into provision monitoring.

The reject-inference layer is also a transparent demonstration. The public dataset contains outcomes for all applications, so the project can backtest how well PD parceling approximates hidden rejected-account outcomes. In a real lender setting, rejected outcomes would require later performance data, bureau refreshes, or an approved inference policy.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m credit_risk_au.train --source openml
python -m credit_risk_au.portfolio --accounts 3000
python -m credit_risk_au.analytics
streamlit run app.py
pytest
```

### VS Code Local Workspace

Open the repository folder in VS Code and accept the recommended Python, Ruff, and Docker extensions. The checked-in workspace configuration selects `.venv`, enables pytest discovery, and provides these menu actions:

- **Terminal > Run Task > Environment: install project** installs the editable development environment.
- **Terminal > Run Task > Pipeline: refresh demo artifacts** runs offline model training, portfolio generation, and portfolio analytics in sequence.
- **Run and Debug > Dashboard: Streamlit** starts the local control room with the debugger attached.
- **Terminal > Run Task > Docker: deploy dashboard** builds and starts the container through Docker Compose.

The VS Code native debugger uses port 8504 and the VS Code Docker task uses port 8505, allowing both modes to be tested without collision. Direct Streamlit and Docker Compose commands retain the standard port 8501 default.

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
- `reports/local_reason_codes.csv`
- `reports/fairness_audit.csv`
- `reports/model_registry.json`
- `reports/model_governance_report.md`
- `reports/figures/*.png`
- `models/credit_risk_model.joblib`
- `data/processed/scored_test_applications.csv`
- `data/processed/credit_risk_demo.sqlite`

The portfolio command writes:

- `data/processed/australian_macro_monthly.csv`
- `data/processed/portfolio_accounts.csv`
- `data/processed/portfolio_monthly_performance.csv`
- `reports/portfolio_data_profile.json`

The analytics command writes portfolio risk outputs for monthly arrears, vintage curves, roll rates, population stability, stress scenarios, and IFRS 9-style provisioning to `reports/portfolio/`, with a local SQLite review database and six presentation-ready figures.

The same command now also writes:

- `reports/reject_inference_strategy.csv`
- `reports/reject_inference_by_decile.csv`
- `reports/challenger_monitoring.csv`
- `reports/model_monitoring_alerts.csv`
- `reports/model_monitoring_summary.json`
- `reports/portfolio/ifrs9_ecl_account_snapshot.csv`
- `reports/portfolio/ifrs9_ecl_stage_summary.csv`
- `reports/portfolio/ifrs9_ecl_segment_summary.csv`
- `reports/portfolio/ifrs9_ecl_monthly_movement.csv`
- `reports/figures/portfolio_ifrs9_coverage.png`
- `reports/figures/portfolio_ifrs9_provision_movement.png`

The Streamlit control room presents executive portfolio KPIs, vintage and roll-rate analysis, IFRS 9-style provisioning, model validation, reject-inference sensitivity, challenger monitoring alerts, stress scenarios, segment diagnostics, and individual PD reason codes from the checked report artifacts.

Docker dashboard:

```bash
docker build -t au-credit-risk-analytics .
docker run --rm -p 8501:8501 au-credit-risk-analytics
```

VS Code and Docker Compose deployment:

```bash
docker compose up --build --detach
docker compose ps
```

The image has been built and health-checked with Docker Desktop and is also built by CI on every change. See [`docs/docker_validation.md`](docs/docker_validation.md) for the verified runtime and a Windows custom-installation note.

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
- Portfolio risk concepts: 30+/90+ DPD, vintage curves, roll and cure rates, write-offs, recoveries, PSI, PD/LGD/EAD expected loss, and scenario stress testing.
- Provisioning concepts: Stage 1/2/3 classification, significant PD uplift, lifetime PD approximation, ECL provision, coverage ratio, and monthly provision movement.
- Policy monitoring concepts: reject inference, approved-only bias, PD parceling, challenger alerts, calibration review, and champion replacement controls.
- Model risk mindset: out-of-fold baseline/challenger selection, locked test policy, calibration, bootstrap uncertainty, interpretability, threshold assumptions, and limitations.
- Governance evidence: versioned model registry, artifact hash, local reason codes, segment fairness diagnostics, monitoring triggers, and explicit use restrictions.
- SQL capability through schema design, monitoring views, and reusable analysis queries.
- Public GitHub readiness: no private data, reproducible commands, tests, and clear artifacts.
- APRA-style project framing: clear demo boundary, control mapping, risk indicators, evidence map, and interview-safe language.

## APRA-style Boundary

This project does not claim to be an APRA-compliant system. It uses APRA-style risk-management structure for a public job-search portfolio:

- Scope and permitted-use boundaries are explicit.
- Public and synthetic data sources are documented.
- Model selection avoids post-hoc locked-test replacement.
- Monitoring alerts trigger review rather than automatic production action.
- Operational repeatability is shown through tests, CI, Docker, and health checks.
- Limitations are documented before interview claims are made.

The full control map is in [`docs/apra_style_framework.md`](docs/apra_style_framework.md).

## Interview Walkthrough

Use [`docs/interview_walkthrough.md`](docs/interview_walkthrough.md) for a recruiter/interviewer-ready walkthrough covering:

- 30-second pitch.
- GitHub live demo path.
- Personal contribution.
- Quantified outputs.
- Defensible A/B claim boundaries.
- Responses to common critiques.
- Project limitations.
- APRA-style boundary language.

## Resume Bullets

- Built an end-to-end credit risk analytics project in Python, selecting a calibrated gradient-boosting champion using five-fold out-of-fold validation and evaluating it once on a locked test set (AUC 0.793; 95% bootstrap CI 0.718-0.860).
- Designed PostgreSQL-ready credit risk tables and monitoring views for scored applications, approval rate tracking, and model validation reporting.
- Built a 105,520-row monthly account-performance mart and PostgreSQL monitoring layer covering vintage defaults, delinquency migration, portfolio arrears, and expected loss under three stress scenarios.
- Added IFRS 9-style ECL staging and provision analytics across 1,675 active accounts, estimating AUD 291.8k total provision and showing Stage 3 accounts contribute 21.5% of provision from 1.7% of exposure.
- Added reject-inference and challenger-monitoring controls, showing approved-only bad rate of 11.1% versus 30.8% PD-parcelled through-the-door risk and flagging five model-review alerts without post-hoc champion replacement.
- Implemented reproducible data ingestion, feature preprocessing, cost-sensitive thresholding, model explainability, automated tests, and public GitHub documentation for banking/FinTech risk analyst roles.

The concise one-bullet version and defensible interview answers are in [`docs/interview_guide.md`](docs/interview_guide.md), with the full live-demo walkthrough in [`docs/interview_walkthrough.md`](docs/interview_walkthrough.md). The full project history is recorded in [`CHANGELOG.md`](CHANGELOG.md).

## Next Steps

- Add an Australian macroeconomic overlay and monthly account-performance portfolio.
- Add vintage, roll-rate, expected-loss, and population-stability monitoring.
- Add a Streamlit dashboard for score-band monitoring and manual underwriting review.
- Add adverse-action reason-code policy documentation and scheduled production-style monitoring reports.
- Replace the demo dataset with an Australian lender-approved internal dataset if used in a private workplace setting.
