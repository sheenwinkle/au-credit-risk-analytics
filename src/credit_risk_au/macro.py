from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from credit_risk_au.config import PROCESSED_DIR, RAW_DIR, ensure_project_dirs


@dataclass(frozen=True)
class MacroSeries:
    name: str
    table: str
    series_id: str
    url: str
    attribution: str


SERIES = (
    MacroSeries(
        "cash_rate_pct",
        "F1.1",
        "FIRMMCRT",
        "https://www.rba.gov.au/statistics/tables/csv/f1.1-data.csv",
        "Source: Reserve Bank of Australia",
    ),
    MacroSeries(
        "unemployment_rate_pct",
        "H5",
        "GLFSURSA",
        "https://www.rba.gov.au/statistics/tables/csv/h5-data.csv",
        "Source: Australian Bureau of Statistics",
    ),
    MacroSeries(
        "inflation_year_ended_pct",
        "G1",
        "GCPIAGYP",
        "https://www.rba.gov.au/statistics/tables/csv/g1-data.csv",
        "Based on Australian Bureau of Statistics data",
    ),
    MacroSeries(
        "personal_credit_growth_yoy_pct",
        "D1",
        "DGFACOP12",
        "https://www.rba.gov.au/statistics/tables/csv/d1-data.csv",
        "Source: Reserve Bank of Australia",
    ),
)


def download_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": "au-credit-risk-analytics/0.2"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig")


def parse_rba_series(text: str, series_id: str, name: str) -> pd.DataFrame:
    rows = list(csv.reader(io.StringIO(text)))
    series_row_index = next(
        index for index, row in enumerate(rows) if row and row[0].strip() == "Series ID"
    )
    series_row = rows[series_row_index]
    if series_id not in series_row:
        raise ValueError(f"Series ID {series_id!r} was not found in the RBA table")
    column_index = series_row.index(series_id)

    observations = []
    for row in rows[series_row_index + 1 :]:
        if len(row) <= column_index or not row[0].strip():
            continue
        date = pd.to_datetime(row[0], dayfirst=True, errors="coerce")
        value = pd.to_numeric(row[column_index], errors="coerce")
        if pd.notna(date) and pd.notna(value):
            observations.append({"month": date.to_period("M").to_timestamp("M"), name: value})
    if not observations:
        raise ValueError(f"No observations parsed for {series_id!r}")
    return pd.DataFrame(observations).drop_duplicates("month").sort_values("month")


def generate_demo_macro(start: str = "2018-01-31", periods: int = 102) -> pd.DataFrame:
    month = pd.date_range(start, periods=periods, freq="ME")
    index = np.arange(periods)
    pandemic = np.exp(-((index - 28) ** 2) / 28)
    tightening = 1 / (1 + np.exp(-(index - 53) / 5))
    frame = pd.DataFrame(
        {
            "month": month,
            "cash_rate_pct": np.clip(1.5 - 1.4 * pandemic + 2.85 * tightening, 0.1, None),
            "unemployment_rate_pct": 5.2 + 2.1 * pandemic - 1.1 * tightening,
            "inflation_year_ended_pct": 1.8 + 5.0 * np.exp(-((index - 55) ** 2) / 90),
            "personal_credit_growth_yoy_pct": -2.0 * pandemic + 4.0 * tightening,
        }
    )
    numeric_columns = frame.columns.drop("month")
    frame[numeric_columns] = frame[numeric_columns].round(3)
    return frame


def build_macro_panel(allow_fallback: bool = True) -> tuple[pd.DataFrame, dict]:
    ensure_project_dirs()
    frames = []
    sources = []
    try:
        for spec in SERIES:
            text = download_text(spec.url)
            (RAW_DIR / f"rba_{spec.table.lower().replace('.', '_')}.csv").write_text(
                text, encoding="utf-8"
            )
            frames.append(parse_rba_series(text, spec.series_id, spec.name).set_index("month"))
            sources.append(
                {
                    "series": spec.name,
                    "table": spec.table,
                    "series_id": spec.series_id,
                    "url": spec.url,
                    "attribution": spec.attribution,
                }
            )
        panel = pd.concat(frames, axis=1).sort_index()
        panel = panel.loc[panel.index >= "2000-01-01"]
        monthly_index = pd.date_range(panel.index.min(), panel.index.max(), freq="ME")
        panel = panel.reindex(monthly_index).ffill().dropna().rename_axis("month").reset_index()
        source_type = "official_rba_abs"
    except (OSError, TimeoutError, ValueError) as error:
        if not allow_fallback:
            raise
        panel = generate_demo_macro()
        source_type = "synthetic_fallback"
        sources = [{"warning": f"Official download unavailable: {type(error).__name__}"}]

    output_path = PROCESSED_DIR / "australian_macro_monthly.csv"
    panel.to_csv(output_path, index=False)
    metadata = {
        "source_type": source_type,
        "rows": len(panel),
        "start_month": str(panel["month"].min().date()),
        "end_month": str(panel["month"].max().date()),
        "sources": sources,
        "output_path": str(output_path),
    }
    return panel, metadata
