from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from credit_risk_au.config import FIGURES_DIR, PROCESSED_DIR, REPORTS_DIR, ensure_project_dirs
from credit_risk_au.portfolio import build_portfolio

PORTFOLIO_REPORT_DIR = REPORTS_DIR / "portfolio"
STATUS_ORDER = ["CURRENT", "DPD30", "DPD60", "DPD90", "DEFAULT"]


def load_portfolio_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    accounts_path = PROCESSED_DIR / "portfolio_accounts.csv"
    performance_path = PROCESSED_DIR / "portfolio_monthly_performance.csv"
    if not accounts_path.exists() or not performance_path.exists():
        build_portfolio()
    accounts = pd.read_csv(accounts_path, parse_dates=["origination_month"])
    performance = pd.read_csv(performance_path, parse_dates=["reporting_month"])
    return accounts, performance


def monthly_summary(accounts: pd.DataFrame, performance: pd.DataFrame) -> pd.DataFrame:
    enriched = performance.merge(
        accounts[["account_id", "product_type", "state", "risk_band"]],
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    enriched["balance_30_plus"] = enriched["closing_balance"].where(
        enriched["days_past_due"] >= 30, 0
    )
    enriched["balance_90_plus"] = enriched["closing_balance"].where(
        enriched["days_past_due"] >= 90, 0
    )
    summary = (
        enriched.groupby("reporting_month", observed=True)
        .agg(
            active_accounts=("account_id", "nunique"),
            exposure=("closing_balance", "sum"),
            balance_30_plus=("balance_30_plus", "sum"),
            balance_90_plus=("balance_90_plus", "sum"),
            defaults=("default_event", "sum"),
            write_offs=("write_off_amount", "sum"),
            recoveries=("recovery_amount", "sum"),
            expected_loss=("expected_loss", "sum"),
            average_pd=("stressed_pd", "mean"),
        )
        .reset_index()
    )
    summary["balance_30_plus_rate"] = summary["balance_30_plus"] / summary["exposure"]
    summary["balance_90_plus_rate"] = summary["balance_90_plus"] / summary["exposure"]
    summary["expected_loss_rate"] = summary["expected_loss"] / summary["exposure"]
    return summary


def vintage_table(accounts: pd.DataFrame, performance: pd.DataFrame) -> pd.DataFrame:
    origin = accounts[["account_id", "origination_month"]].copy()
    origin["origination_vintage"] = origin["origination_month"].dt.to_period("Q").astype(str)
    cohort_size = origin.groupby("origination_vintage")["account_id"].nunique().rename("originations")
    frame = performance.merge(
        origin[["account_id", "origination_vintage"]],
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    vintage = (
        frame.groupby(["origination_vintage", "months_on_book"], observed=True)
        .agg(
            active_accounts=("account_id", "nunique"),
            defaults_in_month=("default_event", "sum"),
            exposure=("closing_balance", "sum"),
        )
        .reset_index()
        .merge(cohort_size, on="origination_vintage", validate="many_to_one")
    )
    vintage["cumulative_defaults"] = vintage.groupby("origination_vintage")[
        "defaults_in_month"
    ].cumsum()
    vintage["cumulative_default_rate"] = vintage["cumulative_defaults"] / vintage["originations"]
    return vintage


def roll_rate_matrix(performance: pd.DataFrame) -> pd.DataFrame:
    frame = performance.sort_values(["account_id", "reporting_month"]).copy()
    frame["next_status"] = frame.groupby("account_id")["status"].shift(-1)
    transitions = frame.dropna(subset=["next_status"])
    matrix = (
        transitions.groupby(["status", "next_status"], observed=True)
        .size()
        .rename("transitions")
        .reset_index()
    )
    matrix["roll_rate"] = matrix["transitions"] / matrix.groupby("status")[
        "transitions"
    ].transform("sum")
    matrix["status"] = pd.Categorical(matrix["status"], STATUS_ORDER, ordered=True)
    matrix["next_status"] = pd.Categorical(matrix["next_status"], STATUS_ORDER, ordered=True)
    return matrix.sort_values(["status", "next_status"]).reset_index(drop=True)


def population_stability_table(
    performance: pd.DataFrame,
    comparison_months: int = 6,
    bins: int = 10,
) -> pd.DataFrame:
    months = sorted(performance["reporting_month"].unique())
    reference = performance[performance["reporting_month"].isin(months[:comparison_months])]
    current = performance[performance["reporting_month"].isin(months[-comparison_months:])]
    edges = np.unique(reference["stressed_pd"].quantile(np.linspace(0, 1, bins + 1)).to_numpy())
    edges[0], edges[-1] = -np.inf, np.inf

    reference_band = pd.cut(reference["stressed_pd"], bins=edges, include_lowest=True)
    current_band = pd.cut(current["stressed_pd"], bins=edges, include_lowest=True)
    categories = reference_band.cat.categories
    reference_share = reference_band.value_counts(normalize=True).reindex(categories, fill_value=0)
    current_share = current_band.value_counts(normalize=True).reindex(categories, fill_value=0)
    epsilon = 1e-6
    psi_component = (current_share - reference_share) * np.log(
        (current_share + epsilon) / (reference_share + epsilon)
    )
    return pd.DataFrame(
        {
            "pd_band": categories.astype(str),
            "reference_share": reference_share.to_numpy(),
            "current_share": current_share.to_numpy(),
            "psi_component": psi_component.to_numpy(),
            "total_psi": float(psi_component.sum()),
        }
    )


def stress_scenarios(accounts: pd.DataFrame, performance: pd.DataFrame) -> pd.DataFrame:
    latest_month = performance["reporting_month"].max()
    latest = performance[performance["reporting_month"] == latest_month].merge(
        accounts[["account_id", "product_type", "state", "risk_band"]],
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    scenarios = {
        "base": {"pd_multiplier": 1.00, "lgd_uplift": 0.00},
        "moderate": {"pd_multiplier": 1.35, "lgd_uplift": 0.05},
        "severe": {"pd_multiplier": 1.80, "lgd_uplift": 0.12},
    }
    rows = []
    for scenario, assumptions in scenarios.items():
        frame = latest.copy()
        frame["scenario_pd"] = np.minimum(
            1.0, frame["stressed_pd"] * assumptions["pd_multiplier"]
        )
        frame["scenario_lgd"] = np.minimum(1.0, frame["lgd"] + assumptions["lgd_uplift"])
        frame["scenario_expected_loss"] = (
            frame["scenario_pd"] * frame["scenario_lgd"] * frame["ead"]
        )
        grouped = (
            frame.groupby(["product_type", "risk_band"], observed=True)
            .agg(
                accounts=("account_id", "nunique"),
                exposure=("ead", "sum"),
                expected_loss=("scenario_expected_loss", "sum"),
            )
            .reset_index()
        )
        grouped["scenario"] = scenario
        grouped["pd_multiplier"] = assumptions["pd_multiplier"]
        grouped["lgd_uplift"] = assumptions["lgd_uplift"]
        grouped["expected_loss_rate"] = grouped["expected_loss"] / grouped["exposure"]
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True)


def save_portfolio_figures(
    monthly: pd.DataFrame,
    vintage: pd.DataFrame,
    roll_rates: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    fig, left = plt.subplots(figsize=(10, 5.5))
    left.plot(monthly["reporting_month"], monthly["balance_30_plus_rate"], color="#bc4749")
    left.set_ylabel("30+ DPD balance rate")
    left.set_xlabel("")
    right = left.twinx()
    right.plot(monthly["reporting_month"], monthly["exposure"], color="#386641", alpha=0.7)
    right.set_ylabel("Exposure")
    left.set_title("Portfolio exposure and delinquency")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "portfolio_monthly_risk.png", dpi=160)
    plt.close(fig)

    recent_vintages = sorted(vintage["origination_vintage"].unique())[-8:]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for cohort in recent_vintages:
        frame = vintage[vintage["origination_vintage"] == cohort]
        ax.plot(frame["months_on_book"], frame["cumulative_default_rate"], label=cohort)
    ax.set_title("Vintage cumulative default curves")
    ax.set_xlabel("Months on book")
    ax.set_ylabel("Cumulative default rate")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "portfolio_vintage_curves.png", dpi=160)
    plt.close(fig)

    pivot = roll_rates.pivot(index="status", columns="next_status", values="roll_rate").fillna(0)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.heatmap(pivot, annot=True, fmt=".1%", cmap="YlOrRd", ax=ax)
    ax.set_title("Monthly delinquency roll rates")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "portfolio_roll_rates.png", dpi=160)
    plt.close(fig)

    totals = scenarios.groupby("scenario", observed=True)["expected_loss"].sum().reindex(
        ["base", "moderate", "severe"]
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    totals.plot(kind="bar", color=["#386641", "#f4a261", "#bc4749"], ax=ax)
    ax.set_title("Expected loss under stress scenarios")
    ax.set_xlabel("")
    ax.set_ylabel("Expected loss")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "portfolio_stress_expected_loss.png", dpi=160)
    plt.close(fig)


def write_portfolio_sqlite(
    accounts: pd.DataFrame,
    performance: pd.DataFrame,
    monthly: pd.DataFrame,
    roll_rates: pd.DataFrame,
    scenarios: pd.DataFrame,
    db_path: Path,
) -> None:
    with sqlite3.connect(db_path) as conn:
        accounts.to_sql("portfolio_accounts", conn, if_exists="replace", index=False)
        performance.to_sql("monthly_performance", conn, if_exists="replace", index=False)
        monthly.to_sql("monthly_portfolio_summary", conn, if_exists="replace", index=False)
        roll_rates.to_sql("delinquency_roll_rates", conn, if_exists="replace", index=False)
        scenarios.to_sql("stress_scenario_results", conn, if_exists="replace", index=False)


def run_portfolio_analytics() -> dict:
    ensure_project_dirs()
    PORTFOLIO_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    accounts, performance = load_portfolio_data()
    monthly = monthly_summary(accounts, performance)
    vintage = vintage_table(accounts, performance)
    roll_rates = roll_rate_matrix(performance)
    stability = population_stability_table(performance)
    scenarios = stress_scenarios(accounts, performance)

    outputs = {
        "monthly_summary": PORTFOLIO_REPORT_DIR / "monthly_summary.csv",
        "vintage_analysis": PORTFOLIO_REPORT_DIR / "vintage_analysis.csv",
        "roll_rates": PORTFOLIO_REPORT_DIR / "roll_rates.csv",
        "population_stability": PORTFOLIO_REPORT_DIR / "population_stability.csv",
        "stress_scenarios": PORTFOLIO_REPORT_DIR / "stress_scenarios.csv",
    }
    for frame, path in zip(
        [monthly, vintage, roll_rates, stability, scenarios], outputs.values(), strict=True
    ):
        frame.to_csv(path, index=False)

    save_portfolio_figures(monthly, vintage, roll_rates, scenarios)
    db_path = PROCESSED_DIR / "portfolio_risk_demo.sqlite"
    write_portfolio_sqlite(accounts, performance, monthly, roll_rates, scenarios, db_path)

    scenario_totals = scenarios.groupby("scenario")["expected_loss"].sum().to_dict()
    latest = monthly.iloc[-1]
    summary = {
        "latest_reporting_month": str(latest["reporting_month"].date()),
        "accounts": len(accounts),
        "monthly_records": len(performance),
        "latest_exposure": float(latest["exposure"]),
        "latest_30_plus_rate": float(latest["balance_30_plus_rate"]),
        "latest_90_plus_rate": float(latest["balance_90_plus_rate"]),
        "total_defaults": int(performance["default_event"].sum()),
        "population_stability_index": float(stability["total_psi"].iloc[0]),
        "scenario_expected_loss": {key: float(value) for key, value in scenario_totals.items()},
        "severe_vs_base_el_increase": float(
            scenario_totals["severe"] / scenario_totals["base"] - 1
        ),
        "outputs": {key: str(value) for key, value in outputs.items()},
        "sqlite_demo": str(db_path),
    }
    (REPORTS_DIR / "portfolio_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    argparse.ArgumentParser(description="Run portfolio risk analytics.").parse_args()
    summary = run_portfolio_analytics()
    print(
        "Completed portfolio analytics | "
        f"exposure={summary['latest_exposure']:.0f} | "
        f"30+ DPD={summary['latest_30_plus_rate']:.2%} | "
        f"PSI={summary['population_stability_index']:.3f}"
    )


if __name__ == "__main__":
    main()

