# Interview Walkthrough and Project Value

This guide is written for live interviews, recruiter screens, and GitHub reviews. It explains the value of the project, the path to demonstrate it, and the boundaries that keep the story credible. For the APRA-style control map behind the project framing, see [`apra_style_framework.md`](apra_style_framework.md).

## 30-second Pitch

I built an end-to-end Australian credit risk analytics project that connects application PD modelling, reject-inference sensitivity, challenger monitoring, portfolio monitoring, stress testing, and IFRS 9-style ECL provisioning. It is a public portfolio project, not a production or compliance system, but it is organised with APRA-style risk-management habits: clear scope, evidence, controls, thresholds, limitations, and escalation paths. The latest run covers 3,000 synthetic Australian-labelled accounts and 105,520 account-month observations, with reproducible Python, SQL, Streamlit, Docker, CI, and dashboard outputs.

## GitHub Live Demo Path

Use this order in a live screen share:

1. Open `README.md`
   - Show the business problem, project structure, latest results, and resume bullets.
   - Point out the quality badge to show CI is not decorative.

2. Open `docs/apra_style_framework.md`
   - Show the boundary first: APRA-style framing, not APRA compliance.
   - Show the control framework and evidence map.

3. Open `app.py` or launch the dashboard
   - Local Docker path: `docker compose up --build --detach`
   - Local URL: `http://localhost:8505/` when using the VS Code Docker task in this workspace.
   - Walk through: Executive view -> Portfolio performance -> IFRS 9 provisioning -> Model validation -> Policy monitoring -> Governance.

4. Open `reports/portfolio_summary.json`
   - Show the quantified portfolio outputs: exposure, arrears, stress loss, PSI, ECL provision, reject inference, and monitoring-alert summary.

5. Open `src/credit_risk_au/analytics.py`
   - Show that the portfolio metrics, roll rates, stress scenarios, and ECL staging are implemented as reusable Python functions rather than manually created slides.

6. Open `sql/02_monitoring_views.sql`
   - Show PostgreSQL-ready reporting views for score monitoring, validation lift, reject inference, model alerts, arrears, vintage performance, roll rates, and IFRS 9-style provision summaries.

7. Open `tests/`
   - Show that modelling, governance, portfolio analytics, macro data, app loading, and ECL staging are covered by automated tests.

8. Open `.github/workflows/ci.yml`
   - Show that GitHub Actions checks linting, tests, offline pipeline execution, VS Code workspace JSON, and Docker image build.

## Personal Contribution

This project demonstrates that I can take a vague risk-analytics business problem and turn it into a reproducible analytical product. My contribution covers:

- Framing the lending-risk problem for Australian banking and FinTech roles.
- Building a Python package with clean data, feature, modelling, evaluation, explainability, portfolio, macro, governance, and analytics modules.
- Implementing baseline and challenger credit-risk models with out-of-fold selection, locked-test evaluation, calibration, thresholding, bootstrap confidence intervals, and challenger-alert governance.
- Adding reject-inference sensitivity analysis to show how approved-only performance monitoring can understate through-the-door application risk.
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
| Approved-only observed bad rate | 11.1% |
| PD-parcelled through-the-door bad rate | 30.8% |
| Hidden-label backtest bad rate | 30.0% |
| Open model monitoring alerts | 5 |
| Challenger locked-test AUC delta | +0.011 versus champion |
| Locked-test AUC | 0.793 |
| AUC bootstrap interval | 0.718-0.860 |
| Automated tests | 12 passing locally in the latest run |

## Value to My Resume

This project supports applications for risk analyst, credit risk analyst, model risk analyst, FinTech analyst, and junior data scientist roles because it shows more than model training. It demonstrates:

- Credit-risk domain literacy: PD, bad rate, approval threshold, deciles, Gini, KS, calibration, vintage curves, roll rates, PSI, LGD, EAD, expected loss, staging, and coverage ratio.
- Policy-monitoring literacy: approved-only bias, reject inference, PD parceling, hidden-label backtesting, challenger review alerts, and champion replacement discipline.
- Practical engineering: package structure, tests, CI, Docker, VS Code workspace, SQL assets, reproducible commands, and public documentation.
- Model-risk judgement: champion selection before locked-test evaluation, uncertainty intervals, governance notes, use restrictions, and honest limitations.
- APRA-style framing: risk appetite demonstration, evidence mapping, monitoring thresholds, data-risk boundaries, and operational-repeatability controls without overstating compliance.
- Business communication: dashboard, executive metrics, interview guide, and defensible resume bullets.

## A/B Claim Boundaries

Use this as a boundary between strong claims and overclaims.

| A: defensible claim | B: avoid saying |
| --- | --- |
| I built a reproducible public credit-risk analytics project. | I built a production bank lending system. |
| I used APRA-style structure to organise risk controls, evidence, thresholds, and limitations. | This project is APRA compliant. |
| I used public credit data and synthetic Australian-labelled account performance data. | I used real Australian bank customer data. |
| I demonstrated the workflow for PD modelling, monitoring, stress testing, and ECL-style provisioning. | I created a statutory IFRS 9 impairment model. |
| I showed reject-inference sensitivity using approved-only, PD parceling, and hidden-label backtesting on public demo data. | I recovered true rejected-customer outcomes for a real lender. |
| I flagged challenger outperformance for review without replacing the champion post-hoc. | I proved the challenger should immediately replace the champion. |
| The model achieved locked-test AUC 0.793 on the public demo dataset. | The model will achieve this performance on a lender's private portfolio. |
| The severe scenario increases expected loss by 123.6% under disclosed assumptions. | I forecasted future Australian credit losses. |
| The high PSI is a monitoring alert requiring decomposition. | The high PSI proves the model has failed. |
| The dashboard and SQL views demonstrate how results can be operationalised. | The project is ready for direct production deployment. |

## Defending Common Critiques

### "Why is the portfolio synthetic?"

Public credit datasets rarely include monthly repayment behaviour, arrears migration, write-offs, recoveries, LGD, EAD, and account-level provisioning fields. I used synthetic account performance so the full portfolio workflow is reproducible and privacy-safe, then connected it to public RBA/ABS macro series to make the scenario layer Australian-relevant.

### "Why use APRA-style language if this is not a compliance project?"

I am targeting Australian risk roles, so I want the project to show the discipline of regulated risk work: scope, evidence, controls, thresholds, limitations, and escalation. I am careful not to claim APRA compliance. The value is that the analytical work is organised in a way a financial-institution reviewer would recognise.

### "Why not use only the best locked-test model?"

The champion was selected using development out-of-fold results before the locked test was viewed. Changing the champion after seeing the locked test would be test-set leakage. I kept the original champion to show model-risk discipline rather than chasing the most flattering test number.

### "What does reject inference add?"

It shows why approved-book monitoring can understate application risk. In the latest run, approved-only observed bad rate is 11.1%, while PD parceling estimates through-the-door bad rate at 30.8%; the demo hidden-label backtest is 30.0%. In production, rejected outcomes would not normally be known, so this is a sensitivity and governance exercise, not a claim that I can observe rejected-account defaults.

### "Why are there five model alerts?"

The alerts are a feature, not a failure. Logistic regression performs slightly better on locked-test AUC, Brier score, and business cost, and the champion's calibration slope needs review. The model-risk decision is to document those alerts, keep the original OOF-selected champion, and require more validation evidence before replacement.

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
- APRA-style control mapping is an interview framing device, not a prudential compliance attestation.
- Fairness and reason-code outputs are analytical diagnostics, not legal adverse-action notices.
- Reject inference uses public demo labels for backtesting; real rejected-applicant inference would need approved bureau/performance data and policy sign-off.
- Challenger alerts identify review actions; they are not automatic champion-replacement rules.
- The project does not yet include scheduled production monitoring or authenticated workflow approvals.

## Five-minute Interview Flow

1. Boundary: "This is a public portfolio project organised with APRA-style controls; it is not a compliance or production claim."
2. Problem: "I wanted to show the full risk workflow, not just a classifier."
3. Data: "Public credit applications plus synthetic monthly account performance linked to public macro series."
4. Model: "Baseline logistic regression and calibrated gradient boosting, selected through out-of-fold validation."
5. Validation: "Locked-test AUC 0.793, bootstrap uncertainty, calibration, threshold cost, gains table."
6. Portfolio: "105,520 account-months with arrears, vintage, roll rates, PSI, stress expected loss."
7. Policy monitoring: "Approved-only bad rate is 11.1%; PD parceling estimates 30.8% through-the-door risk, close to the 30.0% hidden-label backtest."
8. Challenger alerts: "Logistic regression beats the champion on locked-test AUC by 0.011, so I flag review without post-hoc replacement."
9. Provisioning: "Stage 1/2/3 ECL-style provision, AUD 291.8k total provision, Stage 3 concentration visible."
10. Engineering: "SQL views, Streamlit dashboard, Docker deployment, tests, CI, and versioned GitHub history."
