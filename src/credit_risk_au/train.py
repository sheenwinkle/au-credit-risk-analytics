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
    find_cost_sensitive_threshold,
    gains_table,
    save_json,
    score_metrics,
)
from credit_risk_au.explain import logistic_feature_effects, permutation_importance_table
from credit_risk_au.features import split_features_target
from credit_risk_au.modeling import build_baseline_model, build_main_model
from credit_risk_au.plots import save_eda_figures, save_model_figures


def train_pipeline(source: str = "openml") -> dict:
    ensure_project_dirs()
    make_sample_file()
    df, dataset_info = load_dataset(source=source)
    x, y = split_features_target(df)

    x_train, x_temp, y_train, y_temp = train_test_split(
        x,
        y,
        test_size=0.40,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    x_valid, x_test, y_valid, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=RANDOM_STATE,
    )

    baseline = build_baseline_model(x_train)
    baseline.fit(x_train, y_train)
    baseline_valid_pd = baseline.predict_proba(x_valid)[:, 1]
    baseline_threshold = find_cost_sensitive_threshold(y_valid.to_numpy(), baseline_valid_pd)["threshold"]
    baseline_test_pd = baseline.predict_proba(x_test)[:, 1]
    baseline_metrics = score_metrics(y_test.to_numpy(), baseline_test_pd, baseline_threshold)

    main_model = build_main_model(x_train)
    main_model.fit(x_train, y_train)
    valid_pd = main_model.predict_proba(x_valid)[:, 1]
    threshold_result = find_cost_sensitive_threshold(y_valid.to_numpy(), valid_pd)
    test_pd = main_model.predict_proba(x_test)[:, 1]
    main_metrics = score_metrics(y_test.to_numpy(), test_pd, threshold_result["threshold"])

    scored = x_test.copy()
    scored[TARGET] = y_test.to_numpy()
    scored["score_pd"] = test_pd
    scored["approved_flag"] = (scored["score_pd"] < threshold_result["threshold"]).astype(int)
    scored["risk_decile"] = pd.qcut(scored["score_pd"].rank(method="first"), 10, labels=False) + 1
    scored["risk_decile"] = 11 - scored["risk_decile"].astype(int)

    gains = gains_table(y_test.to_numpy(), test_pd)
    importance = permutation_importance_table(main_model, x_test, y_test)
    logistic_effects = logistic_feature_effects(baseline)

    save_eda_figures(df, TARGET, FIGURES_DIR)
    save_model_figures(y_test, test_pd, FIGURES_DIR)

    scored_path = PROCESSED_DIR / "scored_test_applications.csv"
    gains_path = REPORTS_DIR / "gains_table.csv"
    importance_path = REPORTS_DIR / "permutation_importance.csv"
    effects_path = REPORTS_DIR / "baseline_logistic_effects.csv"
    model_path = MODELS_DIR / "credit_risk_model.joblib"
    db_path = PROCESSED_DIR / "credit_risk_demo.sqlite"

    scored.to_csv(scored_path, index=False)
    gains.to_csv(gains_path, index=False)
    importance.to_csv(importance_path, index=False)
    logistic_effects.to_csv(effects_path, index=False)
    joblib.dump(main_model, model_path)
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
        "split": {
            "train_rows": len(x_train),
            "validation_rows": len(x_valid),
            "test_rows": len(x_test),
        },
        "validation_threshold": threshold_result,
        "baseline_logistic": baseline_metrics,
        "main_gradient_boosting": main_metrics,
        "artifacts": {
            "model": str(model_path),
            "scored_test_applications": str(scored_path),
            "gains_table": str(gains_path),
            "permutation_importance": str(importance_path),
            "sqlite_demo": str(db_path),
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
    metrics = payload["main_gradient_boosting"]
    print(
        "Trained credit risk model | "
        f"AUC={metrics['roc_auc']:.3f} | "
        f"Gini={metrics['gini']:.3f} | "
        f"KS={metrics['ks_statistic']:.3f} | "
        f"approval_rate={metrics['approval_rate']:.3f}"
    )


if __name__ == "__main__":
    main()
