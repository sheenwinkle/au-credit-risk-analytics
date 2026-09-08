from sklearn.model_selection import train_test_split

from credit_risk_au.data import generate_synthetic_credit
from credit_risk_au.evaluate import (
    bootstrap_metric_intervals,
    find_cost_sensitive_threshold,
    score_metrics,
    threshold_strategy_table,
)
from credit_risk_au.features import split_features_target
from credit_risk_au.modeling import (
    build_baseline_model,
    build_main_model,
    out_of_fold_probabilities,
)


def test_baseline_and_main_model_produce_probabilities():
    df = generate_synthetic_credit(n_rows=240)
    x, y = split_features_target(df)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, stratify=y, random_state=42)

    baseline = build_baseline_model(x_train).fit(x_train, y_train)
    main = build_main_model(x_train).fit(x_train, y_train)

    for model in [baseline, main]:
        score = model.predict_proba(x_test)[:, 1]
        threshold = find_cost_sensitive_threshold(y_test.to_numpy(), score)["threshold"]
        metrics = score_metrics(y_test.to_numpy(), score, threshold)

        assert score.min() >= 0
        assert score.max() <= 1
        assert 0 <= metrics["roc_auc"] <= 1
        assert 0.05 <= metrics["threshold"] <= 0.95
        assert "calibration_slope" in metrics


def test_oof_validation_and_uncertainty_outputs():
    df = generate_synthetic_credit(n_rows=240)
    x, y = split_features_target(df)
    model = build_baseline_model(x)
    score = out_of_fold_probabilities(model, x, y, folds=3).to_numpy()
    threshold = find_cost_sensitive_threshold(y.to_numpy(), score)["threshold"]

    strategy = threshold_strategy_table(y.to_numpy(), score)
    intervals = bootstrap_metric_intervals(
        y.to_numpy(), score, threshold, n_bootstrap=30
    )

    assert len(score) == len(y)
    assert strategy["threshold"].is_monotonic_increasing
    assert intervals["roc_auc"]["lower_95"] <= intervals["roc_auc"]["estimate"]
    assert intervals["roc_auc"]["estimate"] <= intervals["roc_auc"]["upper_95"]
