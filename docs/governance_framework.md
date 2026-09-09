# Model Risk Governance Framework

## Lifecycle Controls

1. **Development:** preserve source lineage, define the target and intended use, and compare candidates on out-of-fold predictions.
2. **Selection:** freeze the champion and operating threshold before opening the locked test sample.
3. **Validation:** report discrimination, calibration, business-policy outcomes, uncertainty intervals, explainability, and segment diagnostics.
4. **Registration:** record the model version, artifact hash, decision threshold, test results, approval status, and required reviews.
5. **Monitoring:** track score distribution, PSI, calibration, approval rates, segment gaps, arrears, defaults, and expected loss.
6. **Change control:** require revalidation after material data, policy, model, product, or macroeconomic changes.

## Explainability

Global permutation importance shows which source features most affect rank-ordering performance. Local reason codes replace one observed feature at a time with the test-sample median or mode and measure the resulting PD change. This is a transparent sensitivity method but does not establish causality and is not a production adverse-action process.

## Fairness and Responsible Lending

The audit reports approval rate, observed bad rate, average PD, true-positive rate, and false-positive rate for available age and encoded demographic proxy segments. These measures are diagnostic and do not establish legal fairness. Production review would require representative Australian data, legally reviewed protected-attribute handling, minimum segment sizes, uncertainty analysis, policy interaction review, and human oversight.

## Monitoring Thresholds

The project uses review triggers rather than automatic production actions:

- PSI above 0.10: investigate; above 0.25: escalate.
- Calibration slope outside 0.80-1.20 or intercept outside -0.10 to 0.10: investigate.
- ROC AUC decrease greater than 0.05: investigate.
- Material segment approval or error-rate gaps: investigate drivers and policy impacts.

