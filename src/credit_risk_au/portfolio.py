from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from credit_risk_au.config import PROCESSED_DIR, REPORTS_DIR, ensure_project_dirs
from credit_risk_au.macro import build_macro_panel

STATE_DPD = {"CURRENT": 0, "DPD30": 30, "DPD60": 60, "DPD90": 90, "DEFAULT": 120}


def generate_accounts(
    macro: pd.DataFrame,
    n_accounts: int = 3000,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    usable_months = macro["month"].sort_values().iloc[-60:-24].to_numpy()
    products = rng.choice(
        ["personal_loan", "auto_loan", "credit_card"],
        size=n_accounts,
        p=[0.45, 0.35, 0.20],
    )
    original_balance = np.where(
        products == "credit_card",
        rng.lognormal(8.4, 0.5, n_accounts),
        np.where(
            products == "auto_loan",
            rng.lognormal(10.25, 0.38, n_accounts),
            rng.lognormal(9.55, 0.55, n_accounts),
        ),
    )
    risk_score = rng.beta(2.0, 6.5, n_accounts)
    original_pd = np.clip(0.015 + 0.42 * risk_score**2, 0.005, 0.35)
    term = np.where(products == "credit_card", 60, rng.choice([24, 36, 48, 60], n_accounts))
    accounts = pd.DataFrame(
        {
            "account_id": [f"AUS-{value:06d}" for value in range(1, n_accounts + 1)],
            "origination_month": pd.to_datetime(rng.choice(usable_months, n_accounts)),
            "product_type": products,
            "state": rng.choice(
                ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
                n_accounts,
                p=[0.31, 0.26, 0.20, 0.10, 0.07, 0.025, 0.025, 0.01],
            ),
            "original_balance": original_balance.round(2),
            "interest_rate_pct": (
                6.0 + 7.5 * risk_score + np.where(products == "credit_card", 8.0, 0.0)
            ).round(3),
            "term_months": term,
            "original_pd": original_pd.round(6),
            "lgd": np.where(products == "auto_loan", 0.38, 0.62),
        }
    )
    accounts["risk_band"] = pd.cut(
        accounts["original_pd"],
        bins=[0, 0.03, 0.07, 0.15, 1],
        labels=["A", "B", "C", "D"],
        include_lowest=True,
    ).astype(str)
    return accounts.sort_values("account_id").reset_index(drop=True)


def _next_status(current: str, monthly_pd: float, stress: float, draw: float) -> str:
    if current == "CURRENT":
        to_dpd30 = min(0.30, monthly_pd * (1 + stress))
        return "DPD30" if draw < to_dpd30 else "CURRENT"
    if current == "DPD30":
        if draw < max(0.18, 0.42 - stress):
            return "CURRENT"
        return "DPD60" if draw > max(0.55, 0.78 - stress) else "DPD30"
    if current == "DPD60":
        if draw < max(0.08, 0.22 - stress / 2):
            return "DPD30"
        return "DPD90" if draw > max(0.45, 0.68 - stress) else "DPD60"
    if current == "DPD90":
        if draw < 0.10:
            return "DPD60"
        return "DEFAULT" if draw > max(0.35, 0.58 - stress) else "DPD90"
    return "DEFAULT"


def generate_monthly_performance(
    accounts: pd.DataFrame,
    macro: pd.DataFrame,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    macro_frame = macro.copy().set_index("month").sort_index()
    portfolio_end = macro_frame.index.max()
    rows = []

    for account in accounts.itertuples(index=False):
        status = "CURRENT"
        balance = float(account.original_balance)
        month = pd.Timestamp(account.origination_month)
        mob = 0
        while month <= portfolio_end and mob < int(account.term_months) and balance > 1:
            macro_row = macro_frame.loc[month]
            rate_stress = max(0.0, float(macro_row["cash_rate_pct"]) - 2.5) / 8
            labour_stress = max(0.0, float(macro_row["unemployment_rate_pct"]) - 4.5) / 8
            stress = rate_stress + labour_stress
            monthly_pd = 1 - (1 - float(account.original_pd)) ** (1 / 12)
            status = _next_status(status, monthly_pd, stress, rng.random())

            monthly_rate = float(account.interest_rate_pct) / 1200
            scheduled_payment = balance * monthly_rate + float(account.original_balance) / int(
                account.term_months
            )
            payment_factor = {
                "CURRENT": 1.0,
                "DPD30": 0.45,
                "DPD60": 0.20,
                "DPD90": 0.05,
                "DEFAULT": 0.0,
            }[status]
            payment_received = min(balance, scheduled_payment * payment_factor)
            interest = balance * monthly_rate
            closing_balance = max(0.0, balance + interest - payment_received)
            default_event = int(status == "DEFAULT")
            write_off = closing_balance if default_event else 0.0
            recovery = write_off * float(account.lgd) * rng.uniform(0.05, 0.25) if default_event else 0.0
            stressed_pd = min(0.99, float(account.original_pd) * (1 + 1.8 * stress))

            rows.append(
                {
                    "account_id": account.account_id,
                    "reporting_month": month,
                    "months_on_book": mob,
                    "status": status,
                    "days_past_due": STATE_DPD[status],
                    "opening_balance": round(balance, 2),
                    "scheduled_payment": round(scheduled_payment, 2),
                    "payment_received": round(payment_received, 2),
                    "closing_balance": round(closing_balance, 2),
                    "default_event": default_event,
                    "write_off_amount": round(write_off, 2),
                    "recovery_amount": round(recovery, 2),
                    "cash_rate_pct": float(macro_row["cash_rate_pct"]),
                    "unemployment_rate_pct": float(macro_row["unemployment_rate_pct"]),
                    "inflation_year_ended_pct": float(macro_row["inflation_year_ended_pct"]),
                    "personal_credit_growth_yoy_pct": float(
                        macro_row["personal_credit_growth_yoy_pct"]
                    ),
                    "stressed_pd": round(stressed_pd, 6),
                    "lgd": float(account.lgd),
                    "ead": round(closing_balance, 2),
                    "expected_loss": round(stressed_pd * float(account.lgd) * closing_balance, 2),
                }
            )
            balance = closing_balance
            if default_event:
                break
            mob += 1
            month = month + pd.offsets.MonthEnd(1)

    return pd.DataFrame(rows)


def build_portfolio(n_accounts: int = 3000) -> dict:
    ensure_project_dirs()
    macro, macro_metadata = build_macro_panel()
    accounts = generate_accounts(macro, n_accounts=n_accounts)
    performance = generate_monthly_performance(accounts, macro)

    accounts_path = PROCESSED_DIR / "portfolio_accounts.csv"
    performance_path = PROCESSED_DIR / "portfolio_monthly_performance.csv"
    metadata_path = REPORTS_DIR / "portfolio_data_profile.json"
    accounts.to_csv(accounts_path, index=False)
    performance.to_csv(performance_path, index=False)

    metadata = {
        "data_classification": "synthetic account data enriched with public macro series",
        "accounts": len(accounts),
        "monthly_records": len(performance),
        "reporting_months": performance["reporting_month"].nunique(),
        "defaults": int(performance["default_event"].sum()),
        "products": accounts["product_type"].value_counts().to_dict(),
        "macro": macro_metadata,
        "outputs": {
            "accounts": str(accounts_path),
            "monthly_performance": str(performance_path),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Australian credit portfolio data.")
    parser.add_argument("--accounts", type=int, default=3000)
    args = parser.parse_args()
    metadata = build_portfolio(n_accounts=args.accounts)
    print(
        "Built portfolio data | "
        f"accounts={metadata['accounts']} | "
        f"monthly_records={metadata['monthly_records']} | "
        f"defaults={metadata['defaults']}"
    )


if __name__ == "__main__":
    main()

