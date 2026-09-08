-- Highest-risk bands for policy review or manual underwriting.
SELECT
    risk_decile,
    applications,
    ROUND(avg_pd::numeric, 4) AS avg_pd,
    ROUND(observed_bad_rate::numeric, 4) AS observed_bad_rate
FROM credit_risk.validation_gains
WHERE risk_decile <= 3
ORDER BY risk_decile;

-- Portfolio approval monitoring by score band.
SELECT
    risk_decile,
    applications,
    ROUND(approval_rate::numeric, 4) AS approval_rate,
    ROUND(avg_pd::numeric, 4) AS avg_pd
FROM credit_risk.v_score_monitoring
ORDER BY risk_decile;

-- Model validation lift table.
SELECT
    risk_decile,
    applications,
    bads,
    ROUND(avg_pd::numeric, 4) AS avg_pd,
    ROUND(observed_bad_rate::numeric, 4) AS observed_bad_rate,
    ROUND(lift_vs_portfolio::numeric, 2) AS lift_vs_portfolio
FROM credit_risk.v_validation_lift;
