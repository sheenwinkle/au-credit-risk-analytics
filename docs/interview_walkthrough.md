# Interview Walkthrough and Project Value

This guide is written for live interviews, recruiter screens, and GitHub reviews. It explains the value of the project, the path to demonstrate it, and the boundaries that keep the story credible.

## 30-second Pitch

I built an end-to-end Australian credit risk analytics project that connects application PD modelling, portfolio monitoring, stress testing, and IFRS 9-style ECL provisioning. The project uses Python, SQL, Streamlit, Docker, and CI to show the full workflow a bank or FinTech risk analyst would be expected to understand: model development, validation, score monitoring, vintage and roll-rate analysis, expected loss, provisioning, documentation, and governance controls. The latest run covers 3,000 synthetic Australian-labelled accounts and 105,520 account-month observations, with reproducible outputs and a dashboard that can be reviewed locally or from GitHub.

## GitHub Live Demo Path

Use this order in a live screen share:

1. Open `README.md`
   - Show the business problem, project structure, latest results, and resume bullets.
   - Point out the quality badge to show CI is not decorative.

2. Open `app.py` or launch the dashboard
   - Local Docker path: `docker compose up --build --detach`
   - Local URL: `http://localhost:8505/` when using the VS Code Docker task in this workspace.
   - Walk through: Executive view -> Portfolio performance -> IFRS 9 provisioning -> Model validation -> Governance.

3. Open `reports/portfolio_summary.json`
   - Show the quantified portfolio outputs: exposure, arrears, stress loss, PSI, and ECL provision.

4. Open `src/credit_risk_au/analytics.py`
   - Show that the portfolio metrics, roll rates, stress scenarios, and ECL staging are implemented as reusable Python functions rather than manually created slides.

5. Open `sql/02_monitoring_views.sql`
   - Show PostgreSQL-ready reporting views for score monitoring, validation lift, arrears, vintage performance, roll rates, and IFRS 9-style provision summaries.

6. Open `tests/`
   - Show that modelling, governance, portfolio analytics, macro data, app loading, and ECL staging are covered by automated tests.

7. Open `.github/workflows/ci.yml`
   - Show that GitHub Actions checks linting, tests, offline pipeline execution, VS Code workspace JSON, and Docker image build.

## Personal Contribution

This project demonstrates that I can take a vague risk-analytics business problem and turn it into a reproducible analytical product. My contribution covers:

- Framing the lending-risk problem for Australian banking and FinTech roles.
- Building a Python package with clean data, feature, modelling, evaluation, explainability, portfolio, macro, governance, and analytics modules.
- Implementing baseline and challenger credit-risk models with out-of-fold selection, locked-test evaluation, calibration, thresholding, and bootstrap confidence intervals.
- Designing a monthly account-performance mart with arrears, roll-rate, vintage, write-off, recovery, PD, LGD, EAD, expected-loss, and stress-scenario fields.
- Adding IFRS 9-style Stage 1/2/3 ECL provisioning analytics and explaining the limitations clearly.
- Creating PostgreSQL-ready schema, views, and analysis queries.
- Building a Streamlit control room, local Docker deployment, VS Code tasks, CI checks, and public GitHub documentation.

## Quantified Outputs

Use these numbers when explaining value:

| Area | Output |
| --- | ---: |
| Application data | 1,000 public OpenML/UCI credit records |
| Portfolio scale | 3,000 synthetic Australian-labelled accounts |
| Performance records | 105,520 account-month observations |
| Simulated defaults | 231 |
| Latest exposure | AUD 7.49m |
| Latest 30+ DPD balance rate | 2.87% |
| Latest 90+ DPD balance rate | 1.72% |
| Severe stress expected loss | AUD 520.7k |
| Severe vs base expected-loss uplift | 123.6% |
| Population Stability Index | 2.404 |
| IFRS 9-style total ECL provision | AUD 291.8k |
| Stage 3 provision contribution | 21.5% of provision from 1.7% of exposure |
| Locked-test AUC | 0.793 |
| AUC bootstrap interval | 0.718-0.860 |
| Automated tests | 10 passing locally in the latest run |

## Value to My Resume

This project supports applications for risk analyst, credit risk analyst, model risk analyst, FinTech analyst, and junior data scientist roles because it shows more than model training. It demonstrates:

- Credit-risk domain literacy: PD, bad rate, approval threshold, deciles, Gini, KS, calibration, vintage curves, roll rates, PSI, LGD, EAD, expected loss, staging, and coverage ratio.
- Practical engineering: package structure, tests, CI, Docker, VS Code workspace, SQL assets, reproducible commands, and public documentation.
- Model-risk judgement: champion selection before locked-test evaluation, uncertainty intervals, governance notes, use restrictions, and honest limitations.
- Business communication: dashboard, executive metrics, interview guide, and defensible resume bullets.

## A/B Claim Boundaries

Use this as a boundary between strong claims and overclaims.

| A: defensible claim | B: avoid saying |
| --- | --- |
| I built a reproducible public credit-risk analytics project. | I built a production bank lending system. |
| I used public credit data and synthetic Australian-labelled account performance data. | I used real Australian bank customer data. |
| I demonstrated the workflow for PD modelling, monitoring, stress testing, and ECL-style provisioning. | I created a statutory IFRS 9 impairment model. |
| The model achieved locked-test AUC 0.793 on the public demo dataset. | The model will achieve this performance on a lender's private portfolio. |
| The severe scenario increases expected loss by 123.6% under disclosed assumptions. | I forecasted future Australian credit losses. |
| The high PSI is a monitoring alert requiring decomposition. | The high PSI proves the model has failed. |
| The dashboard and SQL views demonstrate how results can be operationalised. | The project is ready for direct production deployment. |

## Defending Common Critiques

### "Why is the portfolio synthetic?"

Public credit datasets rarely include monthly repayment behaviour, arrears migration, write-offs, recoveries, LGD, EAD, and account-level provisioning fields. I used synthetic account performance so the full portfolio workflow is reproducible and privacy-safe, then connected it to public RBA/ABS macro series to make the scenario layer Australian-relevant.

### "Why not use only the best locked-test model?"

The champion was selected using development out-of-fold results before the locked test was viewed. Changing the champion after seeing the locked test would be test-set leakage. I kept the original champion to show model-risk discipline rather than chasing the most flattering test number.

### "Is the IFRS 9 layer compliant?"

No. It is an analytical approximation for interview demonstration. A production IFRS 9 impairment model would require approved accounting policy, scenario weights, overlays, audit controls, validation, and sign-off. This project shows that I understand the data flow and risk concepts without overstating compliance.

### "What does the high PSI mean?"

It is a monitoring trigger. In this run, later macro-sensitive PD movement and portfolio seasoning shift the active population away from the reference distribution. The right response is decomposition by product, vintage, macro period, and score band, not automatic model replacement.

### "How would this change with real lender data?"

I would replace synthetic performance with approved internal account data, validate data lineage, recalibrate PD and LGD, tune staging policy to the lender's impairment framework, add reject inference if declined applications are used for origination policy, and implement scheduled monitoring with review thresholds.

## Project Limitations

- The account-performance portfolio is synthetic and should not be described as real customer behaviour.
- The public OpenML/UCI application dataset is not Australian and is small by production modelling standards.
- The ECL staging logic is simplified and not an audited IFRS 9 model.
- Stress scenarios use transparent multipliers, not official forecasts.
- The dashboard is a demonstration control room, not an authenticated production application.
- Fairness and reason-code outputs are analytical diagnostics, not legal adverse-action notices.
- The project does not yet include reject inference, challenger drift alerts, or scheduled model monitoring.

## Five-minute Interview Flow

1. Problem: "I wanted to show the full risk workflow, not just a classifier."
2. Data: "Public credit applications plus synthetic monthly account performance linked to public macro series."
3. Model: "Baseline logistic regression and calibrated gradient boosting, selected through out-of-fold validation."
4. Validation: "Locked-test AUC 0.793, bootstrap uncertainty, calibration, threshold cost, gains table."
5. Portfolio: "105,520 account-months with arrears, vintage, roll rates, PSI, stress expected loss."
6. Provisioning: "Stage 1/2/3 ECL-style provision, AUD 291.8k total provision, Stage 3 concentration visible."
7. Engineering: "SQL views, Streamlit dashboard, Docker deployment, tests, CI, and versioned GitHub history."
8. Boundary: "It is a public demonstration project, not a claim of production deployment or statutory compliance."

