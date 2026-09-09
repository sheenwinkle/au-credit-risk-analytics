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

CREATE OR REPLACE VIEW credit_risk.v_monthly_portfolio_risk AS
SELECT
    reporting_month,
    COUNT(DISTINCT account_id) AS active_accounts,
    SUM(closing_balance) AS exposure,
    SUM(closing_balance) FILTER (WHERE days_past_due >= 30)
        / NULLIF(SUM(closing_balance), 0) AS balance_30_plus_rate,
    SUM(closing_balance) FILTER (WHERE days_past_due >= 90)
        / NULLIF(SUM(closing_balance), 0) AS balance_90_plus_rate,
    SUM(default_event) AS defaults,
    SUM(write_off_amount) AS write_offs,
    SUM(recovery_amount) AS recoveries,
    SUM(expected_loss) AS expected_loss
FROM credit_risk.monthly_performance
GROUP BY reporting_month;

CREATE OR REPLACE VIEW credit_risk.v_delinquency_transitions AS
WITH transitions AS (
    SELECT
        account_id,
        reporting_month,
        status,
        LEAD(status) OVER (PARTITION BY account_id ORDER BY reporting_month) AS next_status
    FROM credit_risk.monthly_performance
)
SELECT
    status,
    next_status,
    COUNT(*) AS transitions,
    COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY status) AS roll_rate
FROM transitions
WHERE next_status IS NOT NULL
GROUP BY status, next_status;

CREATE OR REPLACE VIEW credit_risk.v_vintage_performance AS
SELECT
    DATE_TRUNC('quarter', a.origination_month)::DATE AS origination_vintage,
    p.months_on_book,
    COUNT(DISTINCT p.account_id) AS active_accounts,
    SUM(p.default_event) AS defaults_in_month,
    SUM(SUM(p.default_event)) OVER (
        PARTITION BY DATE_TRUNC('quarter', a.origination_month)
        ORDER BY p.months_on_book
    ) AS cumulative_defaults,
    SUM(p.closing_balance) AS exposure
FROM credit_risk.monthly_performance p
JOIN credit_risk.portfolio_accounts a USING (account_id)
GROUP BY DATE_TRUNC('quarter', a.origination_month), p.months_on_book;
