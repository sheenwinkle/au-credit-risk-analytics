from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_loads_checked_report_artifacts():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=30).run()

    assert not app.exception
    assert app.title[0].value == "Credit Risk Control Room"
    assert len(app.tabs) == 4
