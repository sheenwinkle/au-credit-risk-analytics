from __future__ import annotations

import argparse
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

from credit_risk_au.config import (
    FIGURES_DIR,
    MODELS_DIR,
    PROCESSED_DIR,
    RANDOM_STATE,
    REPORTS_DIR,
    TARGET,
    ensure_project_dirs,
)
from credit_risk_au.data import load_dataset, make_sample_file
from credit_risk_au.database import write_sqlite_demo
from credit_risk_au.evaluate import (
    bootstrap_metric_intervals,
    find_cost_sensitive_threshold,
    gains_table,
    save_json,
    score_metrics,
    threshold_strategy_table,
)
from credit_risk_au.explain import logistic_feature_effects, permutation_importance_table
from credit_risk_au.features import split_features_target
from credit_risk_au.modeling import (
    build_baseline_model,
    build_main_model,
    out_of_fold_probabilities,
)
from credit_risk_au.plots import save_eda_figures, save_model_figures


def train_pipeline(source: str = "openml") -> dict:
    ensure_project_dirs()
    make_sample_file()
    df, dataset_info = load_dataset(source=source)
    x, y = split_features_target(df)

    x_development, x_test, y_development, y_test = train_test_split(
        x,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    candidates = {
        "logistic_regression": build_baseline_model(x_development),
        "calibrated_gradient_boosting": build_main_model(x_development),
    }
    selection_results = {}
    for name, model in candidates.items():
        oof_pd = out_of_fold_probabilities(model, x_development, y_development)
        threshold_result = find_cost_sensitive_threshold(y_development.to_numpy(), oof_pd.to_numpy())
        selection_results[name] = {
            "threshold_result": threshold_result,
            "oof_metrics": score_metrics(
                y_development.to_numpy(),
                oof_pd.to_numpy(),
                threshold_result["threshold"],
            ),
            "oof_pd": oof_pd,
        }

    champion_name = min(
        selection_results,
        key=lambda name: (
            selection_results[name]["oof_metrics"]["business_cost_per_application"],
            -selection_results[name]["oof_metrics"]["roc_auc"],
        ),
    )
    fitted_models = {}
    test_results = {}
    test_probabilities = {}
    for name, model in candidates.items():
        model.fit(x_development, y_development)
        fitted_models[name] = model
        test_pd = model.predict_proba(x_test)[:, 1]
        test_probabilities[name] = test_pd
        threshold = selection_results[name]["threshold_result"]["threshold"]
        test_results[name] = score_metrics(y_test.to_numpy(), test_pd, threshold)

    champion_model = fitted_models[champion_name]
    champion_test_pd = test_probabilities[champion_name]
    champion_threshold = selection_results[champion_name]["threshold_result"]["threshold"]

    scored = x_test.copy()
    scored[TARGET] = y_test.to_numpy()
    scored["score_pd"] = champion_test_pd
    scored["approved_flag"] = (scored["score_pd"] < champion_threshold).astype(int)
    scored["risk_decile"] = pd.qcut(scored["score_pd"].rank(method="first"), 10, labels=False) + 1
    scored["risk_decile"] = 11 - scored["risk_decile"].astype(int)

    gains = gains_table(y_test.to_numpy(), champion_test_pd)
    importance = permutation_importance_table(champion_model, x_test, y_test)
    logistic_effects = logistic_feature_effects(fitted_models["logistic_regression"])
    confidence_intervals = bootstrap_metric_intervals(
        y_test.to_numpy(), champion_test_pd, champion_threshold
    )
    threshold_strategy = threshold_strategy_table(
        y_development.to_numpy(), selection_results[champion_name]["oof_pd"].to_numpy()
    )
    comparison = pd.DataFrame(
        [
            {
                "model": name,
                "selected_champion": name == champion_name,
                "selection_threshold": result["threshold_result"]["threshold"],
                "oof_roc_auc": result["oof_metrics"]["roc_auc"],
                "oof_brier_score": result["oof_metrics"]["brier_score"],
                "oof_business_cost_per_application": result["oof_metrics"][
                    "business_cost_per_application"
                ],
                "test_roc_auc": test_results[name]["roc_auc"],
                "test_brier_score": test_results[name]["brier_score"],
                "test_business_cost_per_application": test_results[name][
                    "business_cost_per_application"
                ],
            }
            for name, result in selection_results.items()
        ]
    )

    save_eda_figures(df, TARGET, FIGURES_DIR)
    save_model_figures(y_test, champion_test_pd, FIGURES_DIR)

    scored_path = PROCESSED_DIR / "scored_test_applications.csv"
    gains_path = REPORTS_DIR / "gains_table.csv"
    importance_path = REPORTS_DIR / "permutation_importance.csv"
    effects_path = REPORTS_DIR / "baseline_logistic_effects.csv"
    comparison_path = REPORTS_DIR / "model_comparison.csv"
    threshold_path = REPORTS_DIR / "threshold_strategy.csv"
    intervals_path = REPORTS_DIR / "bootstrap_intervals.json"
    model_path = MODELS_DIR / "credit_risk_model.joblib"
    db_path = PROCESSED_DIR / "credit_risk_demo.sqlite"

    scored.to_csv(scored_path, index=False)
    gains.to_csv(gains_path, index=False)
    importance.to_csv(importance_path, index=False)
    logistic_effects.to_csv(effects_path, index=False)
    comparison.to_csv(comparison_path, index=False)
    threshold_strategy.to_csv(threshold_path, index=False)
    save_json(confidence_intervals, intervals_path)
    joblib.dump(champion_model, model_path)
    write_sqlite_demo(df, scored, gains, db_path)

    payload = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "source": dataset_info.source,
            "rows": dataset_info.rows,
            "columns": dataset_info.columns,
            "bad_rate": dataset_info.bad_rate,
            "processed_path": str(dataset_info.processed_path),
        },
        "validation_design": {
            "development_rows": len(x_development),
            "test_rows": len(x_test),
            "selection_method": "5-fold out-of-fold predictions on development set",
            "test_policy": "locked until champion and threshold were selected",
        },
        "champion_model": champion_name,
        "model_selection": {
            name: {
                "threshold_result": result["threshold_result"],
                "oof_metrics": result["oof_metrics"],
            }
            for name, result in selection_results.items()
        },
        "locked_test_results": test_results,
        "champion_bootstrap_95_intervals": confidence_intervals,
        "artifacts": {
            "model": str(model_path),
            "scored_test_applications": str(scored_path),
            "gains_table": str(gains_path),
            "permutation_importance": str(importance_path),
            "sqlite_demo": str(db_path),
            "model_comparison": str(comparison_path),
            "threshold_strategy": str(threshold_path),
        },
    }
    save_json(payload, REPORTS_DIR / "metrics.json")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the credit risk analytics project.")
    parser.add_argument(
        "--source",
        choices=["openml", "sample", "synthetic"],
        default="openml",
        help="Use OpenML credit-g by default. Sample/synthetic are offline-friendly.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = train_pipeline(source=args.source)
    champion_name = payload["champion_model"]
    metrics = payload["locked_test_results"][champion_name]
    print(
        f"Trained credit risk model | champion={champion_name} | "
        f"AUC={metrics['roc_auc']:.3f} | "
        f"Gini={metrics['gini']:.3f} | "
        f"KS={metrics['ks_statistic']:.3f} | "
        f"approval_rate={metrics['approval_rate']:.3f}"
    )


if __name__ == "__main__":
    main()
