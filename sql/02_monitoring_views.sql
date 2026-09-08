CREATE OR REPLACE VIEW credit_risk.v_score_monitoring AS
SELECT
    risk_decile,
    COUNT(*) AS applications,
    AVG(score_pd) AS avg_pd,
    AVG(CASE WHEN approved_flag = 1 THEN 1.0 ELSE 0.0 END) AS approval_rate
FROM credit_risk.model_scores
GROUP BY risk_decile;

CREATE OR REPLACE VIEW credit_risk.v_validation_lift AS
SELECT
    risk_decile,
    applications,
    bads,
    avg_pd,
    observed_bad_rate,
    observed_bad_rate / NULLIF(AVG(observed_bad_rate) OVER (), 0) AS lift_vs_portfolio
FROM credit_risk.validation_gains
ORDER BY risk_decile;
