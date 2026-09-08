from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")


def save_eda_figures(df: pd.DataFrame, target: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    set_style()

    numeric_columns = df.select_dtypes(include=["number"]).columns.drop(target, errors="ignore")
    if len(numeric_columns) > 0:
        fig, ax = plt.subplots(figsize=(9, 6))
        correlations = df[list(numeric_columns) + [target]].corr(numeric_only=True)[target].drop(target).sort_values()
        correlations.plot(kind="barh", ax=ax, color="#386641")
        ax.set_title("Numeric feature correlation with default flag")
        ax.set_xlabel("Pearson correlation")
        fig.tight_layout()
        fig.savefig(output_dir / "eda_numeric_correlations.png", dpi=160)
        plt.close(fig)

    categorical = [column for column in df.columns if column not in numeric_columns and column != target]
    if categorical:
        column = categorical[0]
        fig, ax = plt.subplots(figsize=(9, 5))
        (
            df.groupby(column, observed=True)[target]
            .mean()
            .sort_values(ascending=False)
            .head(12)
            .plot(kind="bar", ax=ax, color="#577590")
        )
        ax.set_title(f"Observed default rate by {column}")
        ax.set_ylabel("Bad rate")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        fig.savefig(output_dir / "eda_default_rate_by_category.png", dpi=160)
        plt.close(fig)


def save_model_figures(y_true, y_score, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    set_style()

    fpr, tpr, _ = roc_curve(y_true, y_score)
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    prob_true, prob_pred = calibration_curve(y_true, y_score, n_bins=10, strategy="quantile")

    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(fpr, tpr, label="Main model", color="#386641")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#6c757d", label="Random")
    ax.set_title("ROC curve")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "model_roc_curve.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(recall, precision, color="#577590")
    ax.set_title("Precision-recall curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    fig.tight_layout()
    fig.savefig(output_dir / "model_precision_recall_curve.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(prob_pred, prob_true, marker="o", color="#bc4749")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#6c757d")
    ax.set_title("Calibration curve")
    ax.set_xlabel("Mean predicted PD")
    ax.set_ylabel("Observed bad rate")
    fig.tight_layout()
    fig.savefig(output_dir / "model_calibration_curve.png", dpi=160)
    plt.close(fig)
