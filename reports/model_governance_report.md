# Model Governance Report

## Decision Record

- Model version: `credit-risk-pd-0.5.0`
- Champion: `calibrated_gradient_boosting`
- Status: `not_for_production`
- Artifact SHA-256: `f9909104cf1f0aac2130fe158d5a600aa18fb9455828610e35fbd16779b20f94`
- Decision threshold: 0.205

The champion and threshold were selected using five-fold out-of-fold development predictions before the locked test sample was evaluated. Test results did not trigger post-hoc model replacement.

## Performance and Uncertainty

- Locked-test ROC AUC: 0.793
- Bootstrap 95% ROC AUC interval: 0.718-0.860
- Maximum absolute segment approval-rate gap versus portfolio (n >= 20): 18.1%

Segment results are diagnostic only. The source dataset is small, dated, and German; encoded segment definitions are not representative of protected groups in modern Australian lending. Small groups and wide sampling uncertainty prevent compliance conclusions.

## Monitoring Triggers

- Investigate PSI above 0.10; escalate above 0.25.
- Investigate calibration slope outside 0.80-1.20 or intercept outside -0.10 to 0.10.
- Investigate ROC AUC deterioration greater than 0.05 from validation.
- Review any material increase in approval-rate or error-rate gaps by monitored segment.
- Revalidate after material data, policy, product, or macroeconomic change.

## Use Restrictions

This model is a portfolio demonstration and must not be used to approve, decline, price, or communicate an adverse action for a real applicant. Local reason codes are sensitivity explanations against a sample reference value, not causal explanations or production-compliant notices.
