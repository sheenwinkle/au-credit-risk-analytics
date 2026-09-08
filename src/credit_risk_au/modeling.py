from __future__ import annotations

import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from credit_risk_au.features import build_preprocessor


def build_baseline_model(x_train: pd.DataFrame) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(x_train)),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    solver="lbfgs",
                ),
            ),
        ]
    )


def build_main_model(x_train: pd.DataFrame) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(x_train)),
            (
                "model",
                CalibratedClassifierCV(
                    estimator=GradientBoostingClassifier(random_state=42),
                    method="sigmoid",
                    cv=3,
                ),
            ),
        ]
    )


def out_of_fold_probabilities(
    model: Pipeline,
    x: pd.DataFrame,
    y: pd.Series,
    folds: int = 5,
) -> pd.Series:
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    probabilities = cross_val_predict(
        clone(model),
        x,
        y,
        cv=cv,
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]
    return pd.Series(probabilities, index=y.index, name="score_pd")
