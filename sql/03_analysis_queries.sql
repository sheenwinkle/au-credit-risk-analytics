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

-- Latest portfolio arrears, losses and expected loss.
SELECT *
FROM credit_risk.v_monthly_portfolio_risk
ORDER BY reporting_month DESC
LIMIT 12;

-- Roll-forward and cure rates between delinquency states.
SELECT
    status,
    next_status,
    transitions,
    ROUND(roll_rate, 4) AS roll_rate
FROM credit_risk.v_delinquency_transitions
ORDER BY status, next_status;

-- Vintage curves suitable for cohort comparison.
SELECT
    origination_vintage,
    months_on_book,
    active_accounts,
    defaults_in_month,
    cumulative_defaults,
    exposure
FROM credit_risk.v_vintage_performance
WHERE months_on_book <= 24
ORDER BY origination_vintage, months_on_book;
