CREATE SCHEMA IF NOT EXISTS credit_risk;

CREATE TABLE IF NOT EXISTS credit_risk.applications (
    application_id BIGSERIAL PRIMARY KEY,
    source_file TEXT NOT NULL DEFAULT 'credit_g_openml_31',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    default_flag INTEGER NOT NULL CHECK (default_flag IN (0, 1))
);

CREATE TABLE IF NOT EXISTS credit_risk.model_scores (
    score_id BIGSERIAL PRIMARY KEY,
    application_id BIGINT REFERENCES credit_risk.applications(application_id),
    model_version TEXT NOT NULL,
    score_pd NUMERIC(8, 6) NOT NULL CHECK (score_pd >= 0 AND score_pd <= 1),
    risk_decile INTEGER NOT NULL CHECK (risk_decile BETWEEN 1 AND 10),
    approved_flag INTEGER NOT NULL CHECK (approved_flag IN (0, 1)),
    scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS credit_risk.validation_gains (
    model_version TEXT NOT NULL,
    risk_decile INTEGER NOT NULL CHECK (risk_decile BETWEEN 1 AND 10),
    applications INTEGER NOT NULL,
    bads INTEGER NOT NULL,
    avg_pd NUMERIC(8, 6) NOT NULL,
    observed_bad_rate NUMERIC(8, 6) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (model_version, risk_decile)
);

CREATE TABLE IF NOT EXISTS credit_risk.portfolio_accounts (
    account_id TEXT PRIMARY KEY,
    origination_month DATE NOT NULL,
    product_type TEXT NOT NULL,
    state CHAR(3) NOT NULL,
    original_balance NUMERIC(14, 2) NOT NULL CHECK (original_balance >= 0),
    interest_rate_pct NUMERIC(8, 4) NOT NULL,
    term_months INTEGER NOT NULL CHECK (term_months > 0),
    original_pd NUMERIC(10, 8) NOT NULL CHECK (original_pd BETWEEN 0 AND 1),
    lgd NUMERIC(10, 8) NOT NULL CHECK (lgd BETWEEN 0 AND 1),
    risk_band CHAR(1) NOT NULL
);

CREATE TABLE IF NOT EXISTS credit_risk.monthly_performance (
    account_id TEXT NOT NULL REFERENCES credit_risk.portfolio_accounts(account_id),
    reporting_month DATE NOT NULL,
    months_on_book INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('CURRENT', 'DPD30', 'DPD60', 'DPD90', 'DEFAULT')),
    days_past_due INTEGER NOT NULL CHECK (days_past_due IN (0, 30, 60, 90, 120)),
    closing_balance NUMERIC(14, 2) NOT NULL,
    default_event INTEGER NOT NULL CHECK (default_event IN (0, 1)),
    write_off_amount NUMERIC(14, 2) NOT NULL,
    recovery_amount NUMERIC(14, 2) NOT NULL,
    stressed_pd NUMERIC(10, 8) NOT NULL CHECK (stressed_pd BETWEEN 0 AND 1),
    lgd NUMERIC(10, 8) NOT NULL CHECK (lgd BETWEEN 0 AND 1),
    ead NUMERIC(14, 2) NOT NULL,
    expected_loss NUMERIC(14, 2) NOT NULL,
    PRIMARY KEY (account_id, reporting_month)
);

CREATE TABLE IF NOT EXISTS credit_risk.macro_economic (
    reporting_month DATE PRIMARY KEY,
    cash_rate_pct NUMERIC(8, 4),
    unemployment_rate_pct NUMERIC(8, 4),
    inflation_year_ended_pct NUMERIC(8, 4),
    personal_credit_growth_yoy_pct NUMERIC(8, 4)
);

CREATE INDEX IF NOT EXISTS idx_monthly_performance_month
    ON credit_risk.monthly_performance(reporting_month);
CREATE INDEX IF NOT EXISTS idx_monthly_performance_status
    ON credit_risk.monthly_performance(status);
