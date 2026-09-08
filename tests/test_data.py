from credit_risk_au.config import TARGET
from credit_risk_au.data import generate_synthetic_credit, load_dataset


def test_synthetic_credit_has_target_and_mixed_features():
    df = generate_synthetic_credit(n_rows=120)

    assert TARGET in df.columns
    assert df[TARGET].isin([0, 1]).all()
    assert df[TARGET].nunique() == 2
    assert {"loan_amount", "purpose", "credit_history"}.issubset(df.columns)


def test_load_sample_dataset_runs_offline():
    df, info = load_dataset(source="sample")

    assert len(df) >= 50
    assert info.bad_rate > 0
    assert info.processed_path.exists()
