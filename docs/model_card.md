# Model Card and Validation Notes

## Intended Use

This model estimates probability of default for a retail credit application demo. It is a portfolio and employability project, not a production lending system.

The intended audience is a recruiter, hiring manager, or interviewer assessing practical credit risk analytics skills for Australian banking or FinTech roles.

## Data Limitations

The OpenML/UCI German Credit dataset is small and dated. It is useful for demonstrating modelling workflow, score validation, SQL reporting, and model risk thinking, but it should not be interpreted as representative of modern Australian borrowers.

The synthetic fallback is only a deterministic demonstration dataset. It is not evidence of real-world model performance.

## Target Definition

The target is `default_flag`:

- `1`: bad/default-like credit outcome
- `0`: good/non-default-like credit outcome

## Validation Design

The pipeline uses stratified train/validation/test splits:

- Training set fits model parameters.
- Validation set chooses the cost-sensitive threshold.
- Test set reports final metrics.

This separation avoids selecting the operating cutoff on the same rows used for final performance reporting.

## Key Metrics

- ROC AUC: rank-ordering quality across all thresholds.
- Gini: common credit risk transformation of AUC, `2 * AUC - 1`.
- KS: separation between cumulative good and bad distributions.
- Average precision: bad-account retrieval quality under class imbalance.
- Brier score: probability calibration quality.
- Approval rate: share of applications below the decline threshold.
- Approved bad rate: observed default rate among approved accounts.
- Gains table: observed bad-rate concentration across score deciles.

## Threshold Policy

The demo threshold assumes an approved bad account is five times as costly as a declined good account. That is a transparent placeholder for expected loss versus opportunity cost.

A real lender would replace this with product-specific:

- exposure at default,
- loss given default,
- margin/revenue,
- hardship and collections cost,
- risk appetite,
- responsible lending controls,
- protected attribute and fairness review.

## Explainability

The project exports:

- permutation importance for the main gradient boosting model,
- logistic regression coefficients and odds ratios for a transparent baseline.

These are intended to support model validation conversations, not final adverse action notices.

## Production Gaps

Before production use, the following would be required:

- materially larger and current Australian data,
- data lineage and access controls,
- out-of-time validation,
- bias/fairness review,
- population stability monitoring,
- policy override capture,
- champion/challenger governance,
- full documentation aligned to internal model risk standards.
