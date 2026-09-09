from credit_risk_au.analytics import (
    monthly_summary,
    population_stability_table,
    roll_rate_matrix,
    stress_scenarios,
    vintage_table,
)
from credit_risk_au.macro import generate_demo_macro
from credit_risk_au.portfolio import generate_accounts, generate_monthly_performance


def test_portfolio_analytics_produce_consistent_risk_outputs():
    macro = generate_demo_macro(periods=72)
    accounts = generate_accounts(macro, n_accounts=120)
    performance = generate_monthly_performance(accounts, macro)

    monthly = monthly_summary(accounts, performance)
    vintage = vintage_table(accounts, performance)
    roll_rates = roll_rate_matrix(performance)
    stability = population_stability_table(performance)
    scenarios = stress_scenarios(accounts, performance)

    assert monthly["balance_30_plus_rate"].between(0, 1).all()
    assert vintage["cumulative_default_rate"].between(0, 1).all()
    assert roll_rates.groupby("status")["roll_rate"].sum().round(8).eq(1).all()
    assert stability["total_psi"].iloc[0] >= 0
    scenario_totals = scenarios.groupby("scenario")["expected_loss"].sum()
    assert scenario_totals["severe"] > scenario_totals["moderate"]
    assert scenario_totals["moderate"] > scenario_totals["base"]

