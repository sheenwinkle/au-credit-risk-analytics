# Interview Guide

## Project Summary

This project separates two related credit-risk decisions:

1. Application risk: estimate probability of default, compare a transparent baseline with a calibrated challenger, and set a cost-sensitive approval cutoff.
2. Portfolio risk: monitor balances, arrears migration, defaults, recoveries, expected loss, stability, and macroeconomic stress after origination.

## Decisions Worth Discussing

### Why was the champion not changed after test evaluation?

The calibrated gradient-boosting model was selected using development out-of-fold results. Logistic regression happened to perform slightly better on the locked test sample. Changing the champion after observing that result would reuse the test sample for selection and make the reported performance optimistic.

### Why use synthetic account data?

Public application datasets do not contain the monthly repayment, delinquency, write-off, recovery, EAD, and LGD fields required for portfolio analysis. Synthetic records make the full data model reproducible without privacy or licensing claims. Public RBA/ABS macro series provide an authentic Australian scenario layer.

### What does the high PSI mean?

PSI of 2.404 is a monitoring alert. Later high-rate conditions push stressed PD away from the low-risk reference bands, while seasoning and attrition alter the active portfolio. The correct response is decomposition and revalidation, not automatic model replacement.

### Is the 123.6% stress-loss increase a forecast?

No. It is scenario sensitivity under disclosed PD multipliers and LGD uplifts. The assumptions are not RBA forecasts and the account data are synthetic.

## Evidence

- Application model: locked-test AUC 0.793, Gini 0.585, KS 0.507.
- Uncertainty: AUC 95% bootstrap interval 0.718-0.860.
- Portfolio: 3,000 accounts and 105,520 account-month records.
- Monitoring: 2.87% 30+ DPD and 1.72% 90+ DPD balance rates in the latest month.
- Stress: expected loss increases from AUD 232.8k to AUD 520.7k in the severe scenario.
- Engineering: package structure, PostgreSQL views, SQLite demo, automated tests, CI, Docker, dashboard, and model registry.

## Resume Bullet

Built a governed credit-risk modelling and portfolio-monitoring platform in Python, SQL, and Streamlit, selecting a calibrated PD model through five-fold out-of-fold validation (locked-test AUC 0.793; 95% CI 0.718-0.860) and analysing 105,520 synthetic account-month records across vintage, roll-rate, PSI, and PD/LGD/EAD stress scenarios.

## Boundaries

Do not describe the synthetic portfolio as bank customer data, the scenario results as forecasts, or the validation results as realised financial savings. The project demonstrates methods, controls, and communication rather than production deployment.

