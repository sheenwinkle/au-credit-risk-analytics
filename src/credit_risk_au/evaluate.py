from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
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
    }


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
