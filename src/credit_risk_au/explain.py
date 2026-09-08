from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline


def permutation_importance_table(
    model: Pipeline,
    x: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 8,
    random_state: int = 42,
    top_n: int = 20,
) -> pd.DataFrame:
    result = permutation_importance(
        model,
        x,
        y,
        scoring="roc_auc",
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=-1,
    )
    frame = pd.DataFrame(
        {
            "feature": x.columns,
            "importance_mean_auc_drop": result.importances_mean,
            "importance_std": result.importances_std,
        }
    )
    return frame.sort_values("importance_mean_auc_drop", ascending=False).head(top_n)


def logistic_feature_effects(model: Pipeline, top_n: int = 20) -> pd.DataFrame:
    preprocess = model.named_steps["preprocess"]
    classifier = model.named_steps["model"]
    names = preprocess.get_feature_names_out()
    coefs = classifier.coef_[0]
    frame = pd.DataFrame(
        {
            "encoded_feature": names,
            "coefficient": coefs,
            "odds_ratio": np.exp(coefs),
            "absolute_coefficient": np.abs(coefs),
        }
    )
    return frame.sort_values("absolute_coefficient", ascending=False).head(top_n)
