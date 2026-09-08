from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    roc_auc_score,
    roc_curve,
)


def ks_statistic(y_true: pd.Series | np.ndarray, y_score: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(tpr - fpr))


def business_cost(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
    fn_cost: float = 5.0,
    fp_cost: float = 1.0,
) -> float:
    pred_bad = (y_score >= threshold).astype(int)
    _tn, fp, fn, _tp = confusion_matrix(y_true, pred_bad, labels=[0, 1]).ravel()
    return float(fn * fn_cost + fp * fp_cost)


def find_cost_sensitive_threshold(
    y_true: np.ndarray,
    y_score: np.ndarray,
    min_approval_rate: float = 0.25,
) -> dict[str, float]:
    thresholds = np.linspace(0.05, 0.95, 181)
    approval_rates = np.array([(y_score < threshold).mean() for threshold in thresholds])
    valid_thresholds = thresholds[approval_rates >= min_approval_rate]
    if len(valid_thresholds) == 0:
        valid_thresholds = thresholds

    costs = np.array([business_cost(y_true, y_score, threshold) for threshold in valid_thresholds])
    best_index = int(np.argmin(costs))
    return {
        "threshold": float(valid_thresholds[best_index]),
        "validation_cost": float(costs[best_index]),
        "min_approval_rate": float(min_approval_rate),
    }


def score_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict[str, float]:
    pred_bad = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred_bad, labels=[0, 1]).ravel()
    approval_mask = pred_bad == 0
    approved_bad_rate = float(y_true[approval_mask].mean()) if approval_mask.any() else 0.0
    declined_bad_rate = float(y_true[pred_bad == 1].mean()) if (pred_bad == 1).any() else 0.0

    calibration = calibration_diagnostics(y_true, y_score)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "gini": float(2 * roc_auc_score(y_true, y_score) - 1),
        "average_precision": float(average_precision_score(y_true, y_score)),
        "brier_score": float(brier_score_loss(y_true, y_score)),
        "log_loss": float(log_loss(y_true, np.clip(y_score, 1e-6, 1 - 1e-6))),
        "ks_statistic": ks_statistic(y_true, y_score),
        "threshold": float(threshold),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
        "approval_rate": float(approval_mask.mean()),
        "approved_bad_rate": approved_bad_rate,
        "declined_bad_rate": declined_bad_rate,
        "business_cost": business_cost(y_true, y_score, threshold),
        "business_cost_per_application": business_cost(y_true, y_score, threshold) / len(y_true),
        **calibration,
    }


def calibration_diagnostics(y_true: np.ndarray, y_score: np.ndarray) -> dict[str, float]:
    clipped = np.clip(y_score, 1e-6, 1 - 1e-6)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    calibrator = LogisticRegression(C=1e6, solver="lbfgs")
    calibrator.fit(logits, y_true)

    frame = pd.DataFrame({"actual": y_true, "score": y_score})
    frame["bin"] = pd.qcut(frame["score"].rank(method="first"), 10, labels=False)
    grouped = frame.groupby("bin", observed=True).agg(
        applications=("actual", "size"),
        observed_rate=("actual", "mean"),
        mean_score=("score", "mean"),
    )
    ece = np.average(
        np.abs(grouped["observed_rate"] - grouped["mean_score"]),
        weights=grouped["applications"],
    )
    return {
        "calibration_intercept": float(calibrator.intercept_[0]),
        "calibration_slope": float(calibrator.coef_[0, 0]),
        "expected_calibration_error": float(ece),
    }


def threshold_strategy_table(
    y_true: np.ndarray,
    y_score: np.ndarray,
    thresholds: np.ndarray | None = None,
) -> pd.DataFrame:
    candidates = thresholds if thresholds is not None else np.linspace(0.05, 0.60, 56)
    rows = []
    for threshold in candidates:
        metrics = score_metrics(y_true, y_score, float(threshold))
        rows.append(
            {
                "threshold": threshold,
                "approval_rate": metrics["approval_rate"],
                "approved_bad_rate": metrics["approved_bad_rate"],
                "false_negative": metrics["false_negative"],
                "false_positive": metrics["false_positive"],
                "business_cost_per_application": metrics["business_cost_per_application"],
            }
        )
    return pd.DataFrame(rows)


def bootstrap_metric_intervals(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    metric_names = [
        "roc_auc",
        "gini",
        "ks_statistic",
        "brier_score",
        "approval_rate",
        "approved_bad_rate",
        "business_cost_per_application",
    ]
    samples = {name: [] for name in metric_names}
    for _ in range(n_bootstrap):
        indexes = rng.integers(0, len(y_true), len(y_true))
        sampled_y = y_true[indexes]
        if np.unique(sampled_y).size < 2:
            continue
        metrics = score_metrics(sampled_y, y_score[indexes], threshold)
        for name in metric_names:
            samples[name].append(metrics[name])

    intervals = {}
    for name, values in samples.items():
        lower, upper = np.quantile(values, [0.025, 0.975])
        intervals[name] = {
            "estimate": float(score_metrics(y_true, y_score, threshold)[name]),
            "lower_95": float(lower),
            "upper_95": float(upper),
        }
    return intervals


def gains_table(y_true: np.ndarray, y_score: np.ndarray, bins: int = 10) -> pd.DataFrame:
    frame = pd.DataFrame({"default_flag": y_true, "score_pd": y_score})
    frame["risk_decile"] = pd.qcut(frame["score_pd"].rank(method="first"), bins, labels=False) + 1
    grouped = (
        frame.groupby("risk_decile", observed=True)
        .agg(
            applications=("default_flag", "size"),
            bads=("default_flag", "sum"),
            avg_pd=("score_pd", "mean"),
            observed_bad_rate=("default_flag", "mean"),
        )
        .reset_index()
    )
    grouped["risk_decile"] = grouped["risk_decile"].astype(int)
    grouped["risk_decile"] = bins + 1 - grouped["risk_decile"]
    return grouped.sort_values("risk_decile")


def save_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
