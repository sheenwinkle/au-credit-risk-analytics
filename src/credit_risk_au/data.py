from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml

from credit_risk_au.config import PROCESSED_DIR, RAW_DIR, SAMPLE_DIR, TARGET, ensure_project_dirs

OPENML_DATA_ID = 31


@dataclass(frozen=True)
class DatasetInfo:
    source: str
    raw_path: Path
    processed_path: Path
    rows: int
    columns: int
    bad_rate: float


def clean_column_name(name: str) -> str:
    cleaned = (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )
    return "_".join(part for part in cleaned.split("_") if part)


def fetch_credit_g() -> pd.DataFrame:
    bunch = fetch_openml(data_id=OPENML_DATA_ID, as_frame=True, parser="auto")
    df = bunch.frame.copy()
    return df


def generate_synthetic_credit(seed: int = 42, n_rows: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    purpose = rng.choice(
        ["car", "education", "home_improvement", "small_business", "consumer_goods"],
        size=n_rows,
        p=[0.28, 0.12, 0.18, 0.16, 0.26],
    )
    employment_status = rng.choice(
        ["permanent", "casual", "contractor", "self_employed"], size=n_rows, p=[0.55, 0.18, 0.15, 0.12]
    )
    age = rng.integers(21, 70, size=n_rows)
    loan_amount = rng.gamma(shape=2.0, scale=4500, size=n_rows).round(0) + 1000
    duration = rng.choice([6, 12, 18, 24, 36, 48, 60], size=n_rows, p=[0.06, 0.18, 0.14, 0.24, 0.22, 0.10, 0.06])
    savings_months = rng.choice([0, 1, 3, 6, 12, 24], size=n_rows, p=[0.18, 0.2, 0.22, 0.2, 0.12, 0.08])
    arrears_12m = rng.poisson(0.35, size=n_rows).clip(0, 4)
    debt_to_income = np.clip(rng.normal(0.32, 0.16, size=n_rows), 0.02, 0.95)
    credit_history = rng.choice(
        ["clean", "minor_arrears", "restructured", "prior_default"],
        size=n_rows,
        p=[0.62, 0.22, 0.10, 0.06],
    )

    logit = (
        -2.4
        + 1.15 * debt_to_income
        + 0.28 * arrears_12m
        + 0.015 * (duration - 24)
        + 0.000045 * loan_amount
        - 0.018 * (age - 35)
        - 0.035 * savings_months
        + np.isin(employment_status, ["casual", "self_employed"]) * 0.38
        + (credit_history == "prior_default") * 1.25
        + (credit_history == "restructured") * 0.72
        + (purpose == "small_business") * 0.28
    )
    pd_prob = 1 / (1 + np.exp(-logit))
    default_flag = rng.binomial(1, pd_prob)

    return pd.DataFrame(
        {
            "age": age,
            "loan_amount": loan_amount.astype(int),
            "duration_months": duration,
            "savings_months": savings_months,
            "arrears_12m": arrears_12m,
            "debt_to_income": debt_to_income.round(3),
            "purpose": purpose,
            "employment_status": employment_status,
            "credit_history": credit_history,
            TARGET: default_flag,
        }
    )


def normalize_credit_g(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [clean_column_name(column) for column in df.columns]

    class_column = "class" if "class" in df.columns else df.columns[-1]
    df[TARGET] = (
        df[class_column]
        .astype(str)
        .str.lower()
        .map({"bad": 1, "good": 0, "1": 1, "2": 0})
        .fillna(df[class_column].astype(str).str.contains("bad", case=False).astype(int))
        .astype(int)
    )
    if class_column != TARGET:
        df = df.drop(columns=[class_column])

    for column in df.columns:
        if column == TARGET:
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.notna().mean() > 0.95:
            df[column] = numeric
        else:
            df[column] = df[column].astype("category")

    return df.dropna(axis=0, how="all")


def make_sample_file(path: Path | None = None) -> Path:
    ensure_project_dirs()
    sample_path = path or SAMPLE_DIR / "sample_applications.csv"
    should_create = True
    if sample_path.exists():
        try:
            should_create = len(pd.read_csv(sample_path, nrows=250)) < 250
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
            should_create = True
    if should_create:
        generate_synthetic_credit(n_rows=600).to_csv(sample_path, index=False)
    return sample_path


def load_dataset(
    source: Literal["openml", "sample", "synthetic"] = "openml",
    allow_fallback: bool = True,
) -> tuple[pd.DataFrame, DatasetInfo]:
    ensure_project_dirs()

    if source == "sample":
        sample_path = make_sample_file()
        raw = pd.read_csv(sample_path)
        processed = normalize_credit_g(raw) if "class" in raw.columns else raw.copy()
        raw_path = sample_path
        source_name = "local sample synthetic credit applications"
    elif source == "synthetic":
        raw = generate_synthetic_credit()
        raw_path = RAW_DIR / "synthetic_credit_applications.csv"
        raw.to_csv(raw_path, index=False)
        processed = raw.copy()
        source_name = "deterministic synthetic credit applications"
    else:
        raw_path = RAW_DIR / "credit_g_openml_31.csv"
        try:
            raw = fetch_credit_g()
            raw.to_csv(raw_path, index=False)
            processed = normalize_credit_g(raw)
            source_name = "OpenML credit-g data_id=31, sourced from UCI Statlog German Credit"
        except Exception:
            if not allow_fallback:
                raise
            raw = generate_synthetic_credit()
            raw_path = RAW_DIR / "synthetic_credit_applications.csv"
            raw.to_csv(raw_path, index=False)
            processed = raw.copy()
            source_name = "synthetic fallback because OpenML was unavailable"

    processed_path = PROCESSED_DIR / "credit_applications_processed.csv"
    processed.to_csv(processed_path, index=False)

    return processed, DatasetInfo(
        source=source_name,
        raw_path=raw_path,
        processed_path=processed_path,
        rows=len(processed),
        columns=len(processed.columns),
        bad_rate=float(processed[TARGET].mean()),
    )
