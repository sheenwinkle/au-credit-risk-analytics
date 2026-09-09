# Changelog

## 0.7.0 - VS Code local workspace

- Added checked-in VS Code settings, recommended extensions, launch configurations, and tasks.
- Added a one-command Docker Compose deployment for the Streamlit control room.
- Added CI validation for workspace JSON and the Compose deployment definition.

## 0.6.1 - Docker runtime verification

- Built the Linux dashboard image with Docker Desktop 4.89.0 and engine 29.7.2.
- Verified container health and the rendered control room on the mapped host port.
- Added a Docker image build to GitHub Actions so packaging is checked on every change.

## 0.6.0 - Engineering and public delivery

- Added offline GitHub Actions quality checks, a Streamlit smoke test, Docker packaging, and complete interview-facing documentation.
- Published a reproducible sequence of scoped Git commits from baseline to portfolio delivery.

## 0.5.0 - Explainability, governance, and control room

- Added individual PD sensitivity reason codes and segment approval/error-rate diagnostics.
- Added model registry metadata, artifact hashing, governance controls, and a four-view Streamlit dashboard.

## 0.4.0 - Portfolio risk and stress analytics

- Added vintage curves, monthly delinquency roll rates, PSI, expected loss, and three stress scenarios.
- Extended PostgreSQL tables and views for account-level monitoring.

## 0.3.0 - Australian macro and account-performance data

- Added official RBA/ABS macro series ingestion with attribution and an offline fallback.
- Added 3,000 synthetic Australian-labelled accounts and 105,520 monthly performance records.

## 0.2.0 - Validation hardening

- Added five-fold out-of-fold model selection, a locked test policy, probability calibration, threshold sensitivity, and bootstrap confidence intervals.

## 0.1.0 - Modelling baseline

- Added public credit data ingestion, cleaning, EDA, logistic and gradient-boosting models, core risk metrics, SQL assets, tests, and documentation.
