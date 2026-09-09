from credit_risk_au.macro import parse_rba_series


def test_parse_rba_series_uses_series_id_not_column_position():
    text = """Example table
Title,Other,Cash Rate Target
Series ID,OTHER,FIRMMCRT
31/01/2024,9.9,4.35
29/02/2024,9.8,4.35
"""
    frame = parse_rba_series(text, "FIRMMCRT", "cash_rate_pct")

    assert frame["cash_rate_pct"].tolist() == [4.35, 4.35]
    assert frame["month"].dt.month.tolist() == [1, 2]

