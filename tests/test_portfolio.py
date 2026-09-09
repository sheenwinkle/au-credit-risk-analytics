from credit_risk_au.macro import generate_demo_macro
from credit_risk_au.portfolio import generate_accounts, generate_monthly_performance


def test_portfolio_panel_has_credit_lifecycle_fields():
    macro = generate_demo_macro(periods=72)
    accounts = generate_accounts(macro, n_accounts=80)
    performance = generate_monthly_performance(accounts, macro)

    assert len(accounts) == 80
    assert len(performance) > len(accounts)
    assert performance["account_id"].isin(accounts["account_id"]).all()
    assert performance["days_past_due"].isin([0, 30, 60, 90, 120]).all()
    assert (performance["expected_loss"] >= 0).all()
    assert (performance.loc[performance["default_event"] == 1, "status"] == "DEFAULT").all()

