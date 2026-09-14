from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def write_sqlite_demo(
    applications: pd.DataFrame,
    scored: pd.DataFrame,
    gains: pd.DataFrame,
    db_path: Path,
    reject_strategy: pd.DataFrame | None = None,
    reject_by_decile: pd.DataFrame | None = None,
    challenger_monitoring: pd.DataFrame | None = None,
    monitoring_alerts: pd.DataFrame | None = None,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        applications.to_sql("applications", conn, if_exists="replace", index=False)
        scored.to_sql("model_scores", conn, if_exists="replace", index=False)
        gains.to_sql("validation_gains", conn, if_exists="replace", index=False)
        if reject_strategy is not None:
            reject_strategy.to_sql("reject_inference_strategy", conn, if_exists="replace", index=False)
        if reject_by_decile is not None:
            reject_by_decile.to_sql("reject_inference_by_decile", conn, if_exists="replace", index=False)
        if challenger_monitoring is not None:
            challenger_monitoring.to_sql("challenger_monitoring", conn, if_exists="replace", index=False)
        if monitoring_alerts is not None:
            monitoring_alerts.to_sql("model_monitoring_alerts", conn, if_exists="replace", index=False)
        conn.execute("DROP VIEW IF EXISTS score_monitoring_summary")
        conn.execute(
            """
            CREATE VIEW score_monitoring_summary AS
            SELECT
                risk_decile,
                COUNT(*) AS applications,
                AVG(score_pd) AS avg_pd,
                AVG(default_flag) AS observed_bad_rate,
                SUM(CASE WHEN approved_flag = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS approval_rate
            FROM model_scores
            GROUP BY risk_decile
            ORDER BY risk_decile
            """
        )
