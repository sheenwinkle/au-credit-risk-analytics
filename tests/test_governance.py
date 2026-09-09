import joblib
from sklearn.model_selection import train_test_split

from credit_risk_au.data import generate_synthetic_credit
from credit_risk_au.features import split_features_target
from credit_risk_au.governance import file_sha256, local_reason_codes, write_model_registry
from credit_risk_au.modeling import build_baseline_model


def test_reason_codes_and_model_registry_are_auditable(tmp_path):
    df = generate_synthetic_credit(n_rows=160)
    x, y = split_features_target(df)
    x_train, x_test, y_train, _ = train_test_split(x, y, test_size=0.2, random_state=42)
    model = build_baseline_model(x_train).fit(x_train, y_train)

    reasons = local_reason_codes(model, x_test, top_n=3)
    model_path = tmp_path / "model.joblib"
    registry_path = tmp_path / "registry.json"
    joblib.dump(model, model_path)
    registry = write_model_registry(registry_path, model_path, {"roc_auc": 0.7}, "test", 0.2)

    assert reasons.groupby("application_row").size().eq(3).all()
    assert reasons["direction"].isin(["increases_risk", "reduces_risk"]).all()
    assert registry["artifact_sha256"] == file_sha256(model_path)
    assert registry_path.exists()

