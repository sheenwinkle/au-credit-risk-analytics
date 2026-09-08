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
