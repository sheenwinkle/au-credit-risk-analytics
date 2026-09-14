from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_rate(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def reject_inference_analysis(scored: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"default_flag", "score_pd", "approved_flag", "risk_decile"}
    missing = required.difference(scored.columns)
    if missing:
        raise ValueError(f"Missing reject inference columns: {sorted(missing)}")

    frame = scored.copy()
    approved = frame[frame["approved_flag"] == 1]
    declined = frame[frame["approved_flag"] == 0]
    total_applications = len(frame)
    approved_bads = float(approved["default_flag"].sum())
    declined_expected_bads = float(declined["score_pd"].sum())
    declined_hidden_bads = float(declined["default_flag"].sum())

    strategy = pd.DataFrame(
        [
            {
                "strategy": "approved_only_observed",
                "population": "approved_accounts_only",
                "applications": len(approved),
                "estimated_bads": approved_bads,
                "estimated_bad_rate": _safe_rate(approved_bads, len(approved)),
                "hidden_validation_bad_rate": _safe_rate(approved_bads, len(approved)),
                "use_case": "Observed book monitoring after accept/decline policy.",
                "limitation": "Ignores rejected applicants and can understate through-the-door risk.",
            },
            {
                "strategy": "pd_parceling",
                "population": "through_the_door_applications",
                "applications": total_applications,
                "estimated_bads": approved_bads + declined_expected_bads,
                "estimated_bad_rate": _safe_rate(
                    approved_bads + declined_expected_bads, total_applications
                ),
                "hidden_validation_bad_rate": _safe_rate(
                    approved_bads + declined_hidden_bads, total_applications
                ),
                "use_case": "Sensitivity estimate for rejected applicants using model PDs.",
                "limitation": "Depends on calibration and does not replace observed rejected outcomes.",
            },
            {
                "strategy": "hidden_outcome_backtest",
                "population": "through_the_door_applications",
                "applications": total_applications,
                "estimated_bads": approved_bads + declined_hidden_bads,
                "estimated_bad_rate": _safe_rate(
                    approved_bads + declined_hidden_bads, total_applications
                ),
                "hidden_validation_bad_rate": _safe_rate(
                    approved_bads + declined_hidden_bads, total_applications
                ),
                "use_case": "Demo-only validation because public data contains all labels.",
                "limitation": "Unavailable in real rejected populations without later performance data.",
            },
        ]
    )

    rows = []
    for decile, group in frame.groupby("risk_decile", observed=True):
        group_approved = group[group["approved_flag"] == 1]
        group_declined = group[group["approved_flag"] == 0]
        rows.append(
            {
                "risk_decile": int(decile),
                "applications": len(group),
                "approved": len(group_approved),
                "declined": len(group_declined),
                "approval_rate": _safe_rate(len(group_approved), len(group)),
                "avg_pd": float(group["score_pd"].mean()),
                "observed_bad_rate": float(group["default_flag"].mean()),
                "approved_observed_bad_rate": float(group_approved["default_flag"].mean())
                if len(group_approved)
                else np.nan,
                "pd_parcelled_declined_bad_rate": float(group_declined["score_pd"].mean())
                if len(group_declined)
                else np.nan,
                "hidden_declined_bad_rate": float(group_declined["default_flag"].mean())
                if len(group_declined)
                else np.nan,
                "expected_declined_bads": float(group_declined["score_pd"].sum()),
                "hidden_declined_bads": float(group_declined["default_flag"].sum()),
            }
        )
    by_decile = pd.DataFrame(rows).sort_values("risk_decile").reset_index(drop=True)
    by_decile["parceling_error_bads"] = (
        by_decile["expected_declined_bads"] - by_decile["hidden_declined_bads"]
    )
    return strategy, by_decile


def challenger_monitoring(
    comparison: pd.DataFrame,
    locked_test_results: dict[str, dict[str, float]],
    champion_model: str,
    auc_delta_watch: float = 0.005,
    brier_delta_watch: float = 0.002,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if champion_model not in locked_test_results:
        raise ValueError(f"Champion model '{champion_model}' not found in locked test results")

    champion_metrics = locked_test_results[champion_model]
    rows = []
    alerts = []
    best_test_auc_model = max(
        locked_test_results,
        key=lambda name: locked_test_results[name]["roc_auc"],
    )
    for row in comparison.to_dict("records"):
        model = str(row["model"])
        test = locked_test_results[model]
        role = "champion" if model == champion_model else "challenger"
        delta_auc = float(test["roc_auc"] - champion_metrics["roc_auc"])
        delta_brier = float(test["brier_score"] - champion_metrics["brier_score"])
        delta_cost = float(
            test["business_cost_per_application"]
            - champion_metrics["business_cost_per_application"]
        )
        rows.append(
            {
                "model": model,
                "role": role,
                "selected_champion": bool(row["selected_champion"]),
                "oof_roc_auc": float(row["oof_roc_auc"]),
                "test_roc_auc": float(test["roc_auc"]),
                "test_brier_score": float(test["brier_score"]),
                "test_business_cost_per_application": float(
                    test["business_cost_per_application"]
                ),
                "delta_test_auc_vs_champion": delta_auc,
                "delta_test_brier_vs_champion": delta_brier,
                "delta_test_cost_vs_champion": delta_cost,
                "calibration_slope": float(test["calibration_slope"]),
                "calibration_intercept": float(test["calibration_intercept"]),
            }
        )
        if role == "challenger" and delta_auc > auc_delta_watch:
            alerts.append(
                {
                    "alert": "challenger_locked_test_auc_above_champion",
                    "model": model,
                    "severity": "watch",
                    "measure": "roc_auc",
                    "delta_vs_champion": delta_auc,
                    "recommended_action": (
                        "Review in the next validation cycle; do not replace the champion "
                        "based only on the locked test sample."
                    ),
                }
            )
        if role == "challenger" and delta_brier < -brier_delta_watch:
            alerts.append(
                {
                    "alert": "challenger_locked_test_brier_below_champion",
                    "model": model,
                    "severity": "watch",
                    "measure": "brier_score",
                    "delta_vs_champion": delta_brier,
                    "recommended_action": "Check calibration stability and sample sensitivity.",
                }
            )
        if role == "challenger" and delta_cost < 0:
            alerts.append(
                {
                    "alert": "challenger_locked_test_cost_below_champion",
                    "model": model,
                    "severity": "watch",
                    "measure": "business_cost_per_application",
                    "delta_vs_champion": delta_cost,
                    "recommended_action": "Re-run OOF validation before any champion replacement.",
                }
            )

    if best_test_auc_model != champion_model:
        alerts.append(
            {
                "alert": "oof_selection_not_confirmed_by_locked_test_auc",
                "model": champion_model,
                "severity": "review",
                "measure": "roc_auc",
                "delta_vs_champion": float(
                    locked_test_results[best_test_auc_model]["roc_auc"]
                    - champion_metrics["roc_auc"]
                ),
                "recommended_action": (
                    "Keep champion selection policy unchanged, document rank-order instability, "
                    "and collect more validation evidence."
                ),
            }
        )

    slope = float(champion_metrics["calibration_slope"])
    if slope < 0.8 or slope > 1.2:
        alerts.append(
            {
                "alert": "champion_calibration_slope_outside_target",
                "model": champion_model,
                "severity": "review",
                "measure": "calibration_slope",
                "delta_vs_champion": slope - 1.0,
                "recommended_action": "Review calibration before production use.",
            }
        )

    monitoring = pd.DataFrame(rows).sort_values(["role", "model"]).reset_index(drop=True)
    alert_frame = pd.DataFrame(alerts)
    if alert_frame.empty:
        alert_frame = pd.DataFrame(
            columns=[
                "alert",
                "model",
                "severity",
                "measure",
                "delta_vs_champion",
                "recommended_action",
            ]
        )
    summary = {
        "champion_model": champion_model,
        "best_locked_test_auc_model": best_test_auc_model,
        "open_alerts": len(alert_frame),
        "review_required": bool(len(alert_frame)),
        "highest_severity": "review"
        if (alert_frame["severity"] == "review").any()
        else ("watch" if len(alert_frame) else "none"),
    }
    return monitoring, alert_frame, summary
