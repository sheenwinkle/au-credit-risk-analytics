# APRA-style Demonstration Boundary and Control Framework

This project is a public portfolio project for Australian banking, FinTech, credit risk, risk analyst, and model risk roles. It is not a production lending system, an APRA compliance attestation, a statutory IFRS 9 impairment model, or a responsible-lending decision engine.

The purpose of this document is narrower and more useful for interviews: it shows how the project is organised using APRA-style prudential risk-management habits, while keeping the evidence, data, and claims appropriate for a public GitHub demonstration.

## Positioning

Use this wording:

> This is a public credit-risk analytics demonstrator built with APRA-style governance, data-risk, model-risk, operational-risk, and monitoring disciplines. It does not claim regulatory compliance or production readiness. It shows that I can structure analytical work in a way that a regulated financial institution would recognise: clear scope, evidence, controls, thresholds, limitations, and escalation paths.

Avoid this wording:

> This project is APRA compliant.

> This project could be used to approve real Australian borrowers.

> This is a production IFRS 9 or responsible-lending model.

## APRA-style Reference Areas

The project uses the following Australian prudential themes as design inspiration:

| Theme | How the project applies it | Boundary |
| --- | --- | --- |
| Risk management framework | Documents model purpose, use restrictions, risk indicators, thresholds, alerts, and issue escalation. | Demonstration only; no board-approved risk appetite statement. |
| Model risk management | Uses baseline/challenger comparison, out-of-fold selection, locked-test discipline, calibration, bootstrap intervals, challenger alerts, and a model registry. | Not independently validated by a second line or model validation team. |
| Data risk management | Separates public/raw/processed/sample data, documents sources, creates reproducible pipelines, and avoids private customer data. | No enterprise data owner, privacy impact assessment, or production data-quality certification. |
| Operational risk and resilience | Uses Docker, CI, VS Code tasks, repeatable commands, smoke tests, and health checks. | No critical-operation approval, recovery time objective, incident management workflow, or supplier contract review. |
| Climate and macro risk | Uses RBA/ABS macro series and stress scenarios for portfolio expected-loss sensitivity. | Scenario multipliers are transparent demo assumptions, not official forecasts or board-approved climate scenarios. |
| Credit policy and responsible lending context | Analyses approval thresholds, bad rates, reject-inference sensitivity, arrears, and loss outcomes. | Does not perform real affordability, suitability, hardship, or customer-level responsible-lending assessment. |

## Control Framework

| Control area | Demonstration control | Evidence in repo |
| --- | --- | --- |
| Scope and permitted use | Explicitly labels all outputs as public demonstration artifacts and prohibits real lending decisions. | `README.md`, `docs/model_card.md`, `docs/interview_walkthrough.md` |
| Data provenance | Documents public OpenML/UCI source, RBA/ABS macro sources, and synthetic account-performance generation. | `docs/data_sources.md`, `src/credit_risk_au/data.py`, `src/credit_risk_au/macro.py`, `src/credit_risk_au/portfolio.py` |
| Data transformation | Keeps reusable cleaning, feature, macro, portfolio, and analytics functions in package modules. | `src/credit_risk_au/` |
| Data quality and reconciliation | Produces deterministic row counts, bad rates, account counts, monthly records, defaults, exposure, and portfolio profiles. | `reports/metrics.json`, `reports/portfolio_data_profile.json`, `reports/portfolio_summary.json` |
| Model development | Compares logistic baseline and calibrated gradient boosting challenger. | `src/credit_risk_au/modeling.py`, `reports/model_comparison.csv` |
| Model selection | Selects champion on development out-of-fold evidence before locked-test evaluation. | `src/credit_risk_au/train.py`, `reports/metrics.json` |
| Model validation | Reports AUC, Gini, KS, Brier score, log loss, calibration diagnostics, gains, bootstrap intervals, threshold cost, and fairness diagnostics. | `reports/metrics.json`, `reports/gains_table.csv`, `reports/bootstrap_intervals.json`, `reports/fairness_audit.csv` |
| Challenger monitoring | Flags locked-test rank-order instability and challenger outperformance without post-hoc champion replacement. | `reports/challenger_monitoring.csv`, `reports/model_monitoring_alerts.csv` |
| Reject inference | Compares approved-only observed risk, PD parceling, and hidden-label backtesting in the public demo sample. | `reports/reject_inference_strategy.csv`, `reports/reject_inference_by_decile.csv` |
| Portfolio monitoring | Tracks arrears, vintage curves, roll rates, PSI, stress expected loss, and ECL-style provision. | `reports/portfolio/`, `src/credit_risk_au/analytics.py` |
| Explainability | Produces permutation importance, logistic feature effects, and local PD sensitivity reason codes. | `reports/permutation_importance.csv`, `reports/baseline_logistic_effects.csv`, `reports/local_reason_codes.csv` |
| Governance record | Registers model version, artifact hash, approval status, decision threshold, reviews, and restrictions. | `reports/model_registry.json`, `reports/model_governance_report.md` |
| Reporting and SQL | Provides PostgreSQL-ready schema, monitoring views, and reusable analysis queries. | `sql/01_postgres_schema.sql`, `sql/02_monitoring_views.sql`, `sql/03_analysis_queries.sql` |
| Operational repeatability | Runs via CLI commands, VS Code tasks, Docker Compose, local tests, and GitHub Actions. | `.vscode/`, `compose.yaml`, `.github/workflows/ci.yml`, `tests/` |

## Risk Appetite Demonstration

These are demonstration thresholds, not board-approved limits:

| Indicator | Demonstration threshold | Current status | Action |
| --- | ---: | ---: | --- |
| PSI | Investigate above 0.10; escalate above 0.25 | 2.404 | Decompose by macro period, product, vintage, and score band. |
| Calibration slope | Review outside 0.80-1.20 | 1.248 | Open model-monitoring alert and review recalibration. |
| Champion AUC deterioration | Review deterioration above 0.05 from validation baseline | No deterioration versus selected locked-test baseline | Continue monitoring. |
| Challenger AUC uplift | Watch if challenger beats champion by more than 0.005 on locked test | +0.011 for logistic regression | Review without post-hoc champion replacement. |
| Approved-only monitoring bias | Review material gap versus through-the-door estimate | 11.1% approved-only bad rate versus 30.8% PD-parcelled bad rate | Keep reject-inference sensitivity in monitoring pack. |
| Stage 3 coverage | Review stage concentration and provision contribution | Stage 3 contributes 21.5% of provision from 1.7% exposure | Explain concentration and portfolio sensitivity. |

## Evidence Map for a Live Interview

1. `README.md`: business problem, results, commands, portfolio relevance, and resume bullets.
2. `docs/apra_style_framework.md`: boundary, APRA-style control map, risk indicators, and evidence.
3. `app.py`: dashboard entry point and tabs for executive, portfolio, provisioning, model validation, policy monitoring, and governance.
4. `reports/metrics.json`: model validation, selection design, locked-test results, and artifacts.
5. `reports/model_monitoring_alerts.csv`: challenger and calibration alerts.
6. `reports/reject_inference_strategy.csv`: approved-only versus through-the-door sensitivity.
7. `reports/portfolio_summary.json`: arrears, exposure, stress expected loss, PSI, and ECL summary.
8. `sql/02_monitoring_views.sql`: database reporting layer.
9. `.github/workflows/ci.yml`: automated lint, tests, offline pipeline, workspace validation, and Docker build.

## Deliberate Non-scope

These exclusions are intentional because the project is public and portfolio-focused:

- No real customer data.
- No production credit decisioning.
- No statutory IFRS 9 compliance claim.
- No APRA compliance attestation.
- No board-approved risk appetite statement.
- No enterprise data owner or second-line validation sign-off.
- No privacy impact assessment or real access-control implementation.
- No responsible-lending affordability assessment.
- No incident-management workflow beyond reproducible local/Docker operation.

## Interview Defence

If asked why the project uses APRA language, answer:

> I use APRA-style structure because I am targeting Australian risk roles, where technical analysis is expected to sit inside a risk-management framework. I am careful not to claim compliance. The value is that the project shows the habit of documenting scope, controls, evidence, thresholds, limitations, and escalation paths.

If asked what remains before real-world use, answer:

> Real-world use would require approved internal data, data ownership, privacy controls, independent validation, responsible-lending review, production monitoring, operational-resilience controls, access management, audit logging, and formal governance sign-off. This project deliberately stops before those claims.

