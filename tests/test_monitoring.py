import pandas as pd

from credit_risk_au.monitoring import challenger_monitoring, reject_inference_analysis


def test_reject_inference_outputs_strategy_and_decile_tables():
    scored = pd.DataFrame(
        {
            "default_flag": [0, 0, 1, 1, 0, 1],
            "score_pd": [0.05, 0.12, 0.22, 0.35, 0.55, 0.72],
            "approved_flag": [1, 1, 0, 0, 0, 0],
            "risk_decile": [10, 9, 5, 4, 2, 1],
        }
    )

    strategy, by_decile = reject_inference_analysis(scored)

    assert set(strategy["strategy"]) == {
        "approved_only_observed",
        "pd_parceling",
        "hidden_outcome_backtest",
    }
    assert by_decile["applications"].sum() == len(scored)
    assert by_decile["declined"].sum() == 4
    assert "parceling_error_bads" in by_decile.columns
    assert strategy.loc[
        strategy["strategy"] == "pd_parceling", "estimated_bad_rate"
    ].iloc[0] > 0


def test_challenger_monitoring_flags_locked_test_instability():
    comparison = pd.DataFrame(
        [
            {
                "model": "champion_model",
                "selected_champion": True,
                "oof_roc_auc": 0.78,
            },
            {
                "model": "challenger_model",
                "selected_champion": False,
                "oof_roc_auc": 0.75,
            },
        ]
    )
    locked_test = {
        "champion_model": {
            "roc_auc": 0.76,
            "brier_score": 0.18,
            "business_cost_per_application": 0.60,
            "calibration_slope": 1.25,
            "calibration_intercept": 0.08,
        },
        "challenger_model": {
            "roc_auc": 0.78,
            "brier_score": 0.17,
            "business_cost_per_application": 0.58,
            "calibration_slope": 0.95,
            "calibration_intercept": -0.02,
        },
    }

    monitoring, alerts, summary = challenger_monitoring(
        comparison,
        locked_test,
        "champion_model",
    )

    assert len(monitoring) == 2
    assert summary["review_required"] is True
    assert summary["best_locked_test_auc_model"] == "challenger_model"
    assert "challenger_locked_test_auc_above_champion" in set(alerts["alert"])
    assert "champion_calibration_slope_outside_target" in set(alerts["alert"])
