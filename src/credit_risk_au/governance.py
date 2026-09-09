from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


def _reference_value(series: pd.Series):
    if pd.api.types.is_numeric_dtype(series):
        return float(series.median())
    modes = series.mode(dropna=True)
    return modes.iloc[0] if not modes.empty else "missing"


def local_reason_codes(
    model: Pipeline,
    x: pd.DataFrame,
    top_n: int = 4,
) -> pd.DataFrame:
    original_pd = model.predict_proba(x)[:, 1]
    impacts = []
    for feature in x.columns:
        counterfactual = x.copy()
        reference = _reference_value(x[feature])
        counterfactual[feature] = reference
        reference_pd = model.predict_proba(counterfactual)[:, 1]
        for position, (row_index, observed) in enumerate(x[feature].items()):
            impacts.append(
                {
                    "application_row": int(row_index),
                    "score_pd": float(original_pd[position]),
                    "feature": feature,
                    "observed_value": str(observed),
                    "reference_value": str(reference),
                    "pd_impact": float(original_pd[position] - reference_pd[position]),
                }
            )
    frame = pd.DataFrame(impacts)
    frame["absolute_impact"] = frame["pd_impact"].abs()
    frame["direction"] = np.where(frame["pd_impact"] >= 0, "increases_risk", "reduces_risk")
    return (
        frame.sort_values(["application_row", "absolute_impact"], ascending=[True, False])
        .groupby("application_row", as_index=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def _segment_metrics(
    frame: pd.DataFrame,
    segment_type: str,
    segment: pd.Series,
) -> pd.DataFrame:
    working = frame.assign(segment=segment.astype(str))
    rows = []
    for value, group in working.groupby("segment", observed=True):
        pred_bad = group["score_pd"] >= group["threshold"]
        actual_bad = group["default_flag"] == 1
        true_positive_rate = float(pred_bad[actual_bad].mean()) if actual_bad.any() else np.nan
        actual_good = ~actual_bad
        false_positive_rate = float(pred_bad[actual_good].mean()) if actual_good.any() else np.nan
        rows.append(
            {
                "segment_type": segment_type,
                "segment": value,
                "applications": len(group),
                "approval_rate": float((~pred_bad).mean()),
                "observed_bad_rate": float(actual_bad.mean()),
                "average_pd": float(group["score_pd"].mean()),
                "true_positive_rate": true_positive_rate,
                "false_positive_rate": false_positive_rate,
            }
        )
    result = pd.DataFrame(rows)
    result["approval_rate_gap_vs_overall"] = result["approval_rate"] - float(
        (frame["score_pd"] < frame["threshold"]).mean()
    )
    return result


def fairness_audit(
    x: pd.DataFrame,
    y_true: pd.Series,
    y_score: np.ndarray,
    threshold: float,
) -> pd.DataFrame:
    frame = x.copy()
    frame["default_flag"] = y_true.to_numpy()
    frame["score_pd"] = y_score
    frame["threshold"] = threshold
    audits = []
    if "age" in frame.columns:
        age_band = pd.cut(
            pd.to_numeric(frame["age"], errors="coerce"),
            bins=[0, 24, 39, 54, np.inf],
            labels=["under_25", "25_39", "40_54", "55_plus"],
        )
        audits.append(_segment_metrics(frame, "age_band", age_band))
    for feature in ["foreign_worker", "personal_status"]:
        if feature in frame.columns:
            audits.append(_segment_metrics(frame, feature, frame[feature]))
    if not audits:
        return pd.DataFrame()
    return pd.concat(audits, ignore_index=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_model_registry(
    path: Path,
    model_path: Path,
    metrics: dict,
    champion_name: str,
    threshold: float,
) -> dict:
    registry = {
        "model_version": "credit-risk-pd-0.5.0",
        "model_name": champion_name,
        "stage": "portfolio_demonstration",
        "approval_status": "not_for_production",
        "artifact_sha256": file_sha256(model_path),
        "decision_threshold": threshold,
        "locked_test_metrics": metrics,
        "required_reviews": [
            "independent model validation",
            "data owner approval",
            "fair lending and responsible lending review",
            "production monitoring sign-off",
        ],
    }
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry


def write_governance_report(
    path: Path,
    registry: dict,
    fairness: pd.DataFrame,
    confidence_intervals: dict,
) -> None:
    eligible_segments = fairness[fairness["applications"] >= 20]
    max_gap = (
        float(eligible_segments["approval_rate_gap_vs_overall"].abs().max())
        if len(eligible_segments)
        else 0
    )
    auc_interval = confidence_intervals["roc_auc"]
    content = f"""# Model Governance Report

## Decision Record

- Model version: `{registry['model_version']}`
- Champion: `{registry['model_name']}`
- Status: `{registry['approval_status']}`
- Artifact SHA-256: `{registry['artifact_sha256']}`
- Decision threshold: {registry['decision_threshold']:.3f}

The champion and threshold were selected using five-fold out-of-fold development predictions before the locked test sample was evaluated. Test results did not trigger post-hoc model replacement.

## Performance and Uncertainty

- Locked-test ROC AUC: {auc_interval['estimate']:.3f}
- Bootstrap 95% ROC AUC interval: {auc_interval['lower_95']:.3f}-{auc_interval['upper_95']:.3f}
- Maximum absolute segment approval-rate gap versus portfolio (n >= 20): {max_gap:.1%}

Segment results are diagnostic only. The source dataset is small, dated, and German; encoded segment definitions are not representative of protected groups in modern Australian lending. Small groups and wide sampling uncertainty prevent compliance conclusions.

## Monitoring Triggers

- Investigate PSI above 0.10; escalate above 0.25.
- Investigate calibration slope outside 0.80-1.20 or intercept outside -0.10 to 0.10.
- Investigate ROC AUC deterioration greater than 0.05 from validation.
- Review any material increase in approval-rate or error-rate gaps by monitored segment.
- Revalidate after material data, policy, product, or macroeconomic change.

## Use Restrictions

This model is a portfolio demonstration and must not be used to approve, decline, price, or communicate an adverse action for a real applicant. Local reason codes are sensitivity explanations against a sample reference value, not causal explanations or production-compliant notices.
"""
    path.write_text(content, encoding="utf-8")
