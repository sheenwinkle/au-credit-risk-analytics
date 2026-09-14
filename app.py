from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
PORTFOLIO_REPORTS = REPORTS / "portfolio"
GREEN = "#386641"
RED = "#bc4749"
AMBER = "#e9a03b"
BLUE = "#457b9d"


@st.cache_data
def load_reports() -> dict:
    return {
        "metrics": json.loads((REPORTS / "metrics.json").read_text(encoding="utf-8")),
        "portfolio": json.loads(
            (REPORTS / "portfolio_summary.json").read_text(encoding="utf-8")
        ),
        "monthly": pd.read_csv(
            PORTFOLIO_REPORTS / "monthly_summary.csv", parse_dates=["reporting_month"]
        ),
        "vintage": pd.read_csv(PORTFOLIO_REPORTS / "vintage_analysis.csv"),
        "roll_rates": pd.read_csv(PORTFOLIO_REPORTS / "roll_rates.csv"),
        "stress": pd.read_csv(PORTFOLIO_REPORTS / "stress_scenarios.csv"),
        "ecl_stage": pd.read_csv(PORTFOLIO_REPORTS / "ifrs9_ecl_stage_summary.csv"),
        "ecl_segment": pd.read_csv(PORTFOLIO_REPORTS / "ifrs9_ecl_segment_summary.csv"),
        "ecl_movement": pd.read_csv(
            PORTFOLIO_REPORTS / "ifrs9_ecl_monthly_movement.csv",
            parse_dates=["reporting_month"],
        ),
        "comparison": pd.read_csv(REPORTS / "model_comparison.csv"),
        "reject_strategy": pd.read_csv(REPORTS / "reject_inference_strategy.csv"),
        "reject_decile": pd.read_csv(REPORTS / "reject_inference_by_decile.csv"),
        "challenger": pd.read_csv(REPORTS / "challenger_monitoring.csv"),
        "monitoring_alerts": pd.read_csv(REPORTS / "model_monitoring_alerts.csv"),
        "monitoring_summary": json.loads(
            (REPORTS / "model_monitoring_summary.json").read_text(encoding="utf-8")
        ),
        "gains": pd.read_csv(REPORTS / "gains_table.csv"),
        "fairness": pd.read_csv(REPORTS / "fairness_audit.csv"),
        "reasons": pd.read_csv(REPORTS / "local_reason_codes.csv"),
        "registry": json.loads((REPORTS / "model_registry.json").read_text(encoding="utf-8")),
    }


def money(value: float) -> str:
    return f"AUD {value / 1_000_000:.2f}m" if value >= 1_000_000 else f"AUD {value / 1_000:.1f}k"


st.set_page_config(page_title="Credit Risk Control Room", page_icon="CR", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {border-left: 3px solid #386641; padding-left: 0.8rem;}
    [data-testid="stMetricLabel"] {font-weight: 600;}
    div[data-baseweb="tab-list"] {gap: 1.2rem;}
    div[data-baseweb="tab"] {padding-left: 0; padding-right: 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

data = load_reports()
portfolio = data["portfolio"]
metrics = data["metrics"]
champion = metrics["champion_model"]
test_metrics = metrics["locked_test_results"][champion]

st.title("Credit Risk Control Room")
st.caption(
    f"Portfolio month {portfolio['latest_reporting_month']}  |  "
    f"Model {data['registry']['model_version']}  |  Demonstration data"
)

with st.sidebar:
    st.subheader("Portfolio Scope")
    st.metric("Accounts", f"{portfolio['accounts']:,}")
    st.metric("Account months", f"{portfolio['monthly_records']:,}")
    st.metric("Simulated defaults", f"{portfolio['total_defaults']:,}")
    st.divider()
    selected_product = st.selectbox(
        "Stress portfolio",
        ["All products"] + sorted(data["stress"]["product_type"].unique().tolist()),
    )
    st.caption("Public RBA/ABS macro series with synthetic account performance")

overview_tab, portfolio_tab, provision_tab, model_tab, monitoring_tab, governance_tab = st.tabs(
    [
        "Executive view",
        "Portfolio performance",
        "IFRS 9 provisioning",
        "Model validation",
        "Policy monitoring",
        "Governance",
    ]
)

with overview_tab:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Exposure", money(portfolio["latest_exposure"]))
    col2.metric("30+ DPD", f"{portfolio['latest_30_plus_rate']:.2%}")
    col3.metric("90+ DPD", f"{portfolio['latest_90_plus_rate']:.2%}")
    col4.metric(
        "Severe EL uplift",
        f"{portfolio['severe_vs_base_el_increase']:.1%}",
        delta_color="inverse",
    )
    ecl_stage = data["ecl_stage"]
    stage_2_3 = ecl_stage[ecl_stage["ifrs9_stage"].isin(["Stage 2", "Stage 3"])]
    ecl_col1, ecl_col2, ecl_col3 = st.columns(3)
    ecl_col1.metric("IFRS 9 provision", money(portfolio["ifrs9_ecl_total_provision"]))
    ecl_col2.metric("Stage 2/3 exposure", money(stage_2_3["exposure"].sum()))
    ecl_col3.metric(
        "Stage 3 coverage",
        f"{portfolio['ifrs9_coverage_by_stage'].get('Stage 3', 0):.1%}",
    )

    monthly = data["monthly"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=monthly["reporting_month"],
            y=monthly["exposure"],
            name="Exposure",
            line={"color": GREEN, "width": 3},
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["reporting_month"],
            y=monthly["balance_30_plus_rate"],
            name="30+ DPD",
            line={"color": RED, "width": 2},
        ),
        secondary_y=True,
    )
    fig.update_yaxes(title_text="Exposure (AUD)", secondary_y=False)
    fig.update_yaxes(title_text="30+ DPD rate", tickformat=".1%", secondary_y=True)
    fig.update_layout(title="Exposure and delinquency", hovermode="x unified", height=430)
    st.plotly_chart(fig, width="stretch")

    stress = data["stress"]
    if selected_product != "All products":
        stress = stress[stress["product_type"] == selected_product]
    stress_total = stress.groupby("scenario", as_index=False)["expected_loss"].sum()
    stress_total["scenario"] = pd.Categorical(
        stress_total["scenario"], ["base", "moderate", "severe"], ordered=True
    )
    stress_total = stress_total.sort_values("scenario")
    stress_fig = px.bar(
        stress_total,
        x="scenario",
        y="expected_loss",
        color="scenario",
        color_discrete_map={"base": GREEN, "moderate": AMBER, "severe": RED},
        title="Expected loss by scenario",
        labels={"scenario": "Scenario", "expected_loss": "Expected loss (AUD)"},
    )
    stress_fig.update_layout(showlegend=False, height=390)
    st.plotly_chart(stress_fig, width="stretch")

with portfolio_tab:
    left, right = st.columns([1.05, 0.95])
    with left:
        vintage = data["vintage"]
        selected_vintages = sorted(vintage["origination_vintage"].unique())[-8:]
        vintage_fig = px.line(
            vintage[vintage["origination_vintage"].isin(selected_vintages)],
            x="months_on_book",
            y="cumulative_default_rate",
            color="origination_vintage",
            title="Vintage cumulative default rate",
            labels={
                "months_on_book": "Months on book",
                "cumulative_default_rate": "Cumulative default rate",
                "origination_vintage": "Vintage",
            },
        )
        vintage_fig.update_yaxes(tickformat=".1%")
        vintage_fig.update_layout(height=470)
        st.plotly_chart(vintage_fig, width="stretch")

    with right:
        roll = data["roll_rates"].pivot(
            index="status", columns="next_status", values="roll_rate"
        ).fillna(0)
        roll = roll.reindex(
            index=["CURRENT", "DPD30", "DPD60", "DPD90"],
            columns=["CURRENT", "DPD30", "DPD60", "DPD90", "DEFAULT"],
            fill_value=0,
        )
        heatmap = px.imshow(
            roll,
            text_auto=".1%",
            color_continuous_scale="YlOrRd",
            title="Monthly delinquency roll rates",
            aspect="auto",
        )
        heatmap.update_layout(height=470, coloraxis_showscale=False)
        st.plotly_chart(heatmap, width="stretch")

    st.dataframe(
        monthly.sort_values("reporting_month", ascending=False).head(12),
        width="stretch",
        hide_index=True,
        column_config={
            "reporting_month": st.column_config.DateColumn("Month"),
            "exposure": st.column_config.NumberColumn("Exposure", format="dollar"),
            "balance_30_plus_rate": st.column_config.NumberColumn("30+ DPD", format="percent"),
            "balance_90_plus_rate": st.column_config.NumberColumn("90+ DPD", format="percent"),
            "expected_loss_rate": st.column_config.NumberColumn("EL rate", format="percent"),
        },
    )

with provision_tab:
    ecl_stage = data["ecl_stage"]
    ecl_segment = data["ecl_segment"]
    ecl_movement = data["ecl_movement"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total provision", money(portfolio["ifrs9_ecl_total_provision"]))
    col2.metric(
        "Stage 2 provision",
        money(portfolio["ifrs9_ecl_by_stage"].get("Stage 2", 0)),
    )
    col3.metric(
        "Stage 3 provision",
        money(portfolio["ifrs9_ecl_by_stage"].get("Stage 3", 0)),
    )
    col4.metric(
        "Stage 2/3 exposure share",
        f"{ecl_stage[ecl_stage['ifrs9_stage'].isin(['Stage 2', 'Stage 3'])]['exposure_share'].sum():.1%}",
    )

    stage_chart = px.bar(
        ecl_stage,
        x="ifrs9_stage",
        y="ecl_provision",
        color="ifrs9_stage",
        color_discrete_map={"Stage 1": GREEN, "Stage 2": AMBER, "Stage 3": RED},
        title="ECL provision by IFRS 9 stage",
        labels={"ifrs9_stage": "Stage", "ecl_provision": "ECL provision (AUD)"},
    )
    stage_chart.update_layout(showlegend=False, height=370)
    st.plotly_chart(stage_chart, width="stretch")

    movement_chart = px.area(
        ecl_movement,
        x="reporting_month",
        y="ecl_provision",
        color="ifrs9_stage",
        color_discrete_map={"Stage 1": GREEN, "Stage 2": AMBER, "Stage 3": RED},
        title="Monthly provision movement",
        labels={
            "reporting_month": "Reporting month",
            "ecl_provision": "ECL provision (AUD)",
            "ifrs9_stage": "Stage",
        },
    )
    movement_chart.update_layout(height=410)
    st.plotly_chart(movement_chart, width="stretch")

    st.dataframe(
        ecl_segment.sort_values("ecl_provision", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "exposure": st.column_config.NumberColumn("Exposure", format="dollar"),
            "average_pd": st.column_config.NumberColumn("Average PD", format="percent"),
            "ecl_provision": st.column_config.NumberColumn("Provision", format="dollar"),
            "coverage_ratio": st.column_config.NumberColumn("Coverage", format="percent"),
        },
    )

with model_tab:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Champion", champion.replace("_", " ").title())
    col2.metric("Locked-test AUC", f"{test_metrics['roc_auc']:.3f}")
    col3.metric("Gini", f"{test_metrics['gini']:.3f}")
    col4.metric("Brier score", f"{test_metrics['brier_score']:.3f}")

    comparison = data["comparison"].copy()
    comparison_chart = comparison.melt(
        id_vars="model",
        value_vars=["oof_roc_auc", "test_roc_auc"],
        var_name="sample",
        value_name="roc_auc",
    )
    comparison_chart["sample"] = comparison_chart["sample"].map(
        {"oof_roc_auc": "Development OOF", "test_roc_auc": "Locked test"}
    )
    model_fig = px.bar(
        comparison_chart,
        x="model",
        y="roc_auc",
        color="sample",
        barmode="group",
        range_y=[0.65, 0.85],
        color_discrete_map={"Development OOF": BLUE, "Locked test": GREEN},
        title="Model discrimination before and after selection",
        labels={"model": "Model", "roc_auc": "ROC AUC", "sample": "Evaluation"},
    )
    model_fig.update_layout(height=410)
    st.plotly_chart(model_fig, width="stretch")

    gains_fig = px.bar(
        data["gains"],
        x="risk_decile",
        y="observed_bad_rate",
        color="avg_pd",
        color_continuous_scale="RdYlGn_r",
        title="Observed bad rate by risk decile",
        labels={"risk_decile": "Risk decile", "observed_bad_rate": "Observed bad rate"},
    )
    gains_fig.update_yaxes(tickformat=".0%")
    gains_fig.update_layout(height=390, coloraxis_colorbar_title="Average PD")
    st.plotly_chart(gains_fig, width="stretch")

with monitoring_tab:
    reject_strategy = data["reject_strategy"]
    reject_decile = data["reject_decile"]
    challenger = data["challenger"]
    alerts = data["monitoring_alerts"]
    monitoring_summary = data["monitoring_summary"]
    approved_only = reject_strategy[
        reject_strategy["strategy"] == "approved_only_observed"
    ].iloc[0]
    parceling = reject_strategy[reject_strategy["strategy"] == "pd_parceling"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Approved-only bad rate", f"{approved_only['estimated_bad_rate']:.1%}")
    col2.metric("PD-parcelled TTD bad rate", f"{parceling['estimated_bad_rate']:.1%}")
    col3.metric("Open model alerts", f"{monitoring_summary['open_alerts']}")
    col4.metric(
        "Best locked-test AUC",
        monitoring_summary["best_locked_test_auc_model"].replace("_", " ").title(),
    )

    reject_chart = px.line(
        reject_decile,
        x="risk_decile",
        y=[
            "avg_pd",
            "observed_bad_rate",
            "pd_parcelled_declined_bad_rate",
            "hidden_declined_bad_rate",
        ],
        markers=True,
        title="Reject inference sensitivity by risk decile",
        labels={"risk_decile": "Risk decile", "value": "Rate", "variable": "Measure"},
    )
    reject_chart.update_yaxes(tickformat=".0%")
    reject_chart.update_layout(height=430)
    st.plotly_chart(reject_chart, width="stretch")

    challenger_chart = px.bar(
        challenger,
        x="model",
        y="delta_test_auc_vs_champion",
        color="role",
        color_discrete_map={"champion": GREEN, "challenger": AMBER},
        title="Locked-test AUC delta versus selected champion",
        labels={"model": "Model", "delta_test_auc_vs_champion": "AUC delta"},
    )
    challenger_chart.update_layout(height=360)
    st.plotly_chart(challenger_chart, width="stretch")

    st.dataframe(
        alerts,
        width="stretch",
        hide_index=True,
        column_config={
            "delta_vs_champion": st.column_config.NumberColumn(
                "Delta vs champion", format="%.4f"
            ),
        },
    )

with governance_tab:
    registry = data["registry"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Model version", registry["model_version"])
    col2.metric("Approval status", registry["approval_status"].replace("_", " ").title())
    col3.metric("Decision threshold", f"{registry['decision_threshold']:.3f}")

    fairness = data["fairness"]
    segment_type = st.selectbox("Segment audit", fairness["segment_type"].unique())
    segment_frame = fairness[fairness["segment_type"] == segment_type]
    fairness_chart = segment_frame.melt(
        id_vars="segment",
        value_vars=["approval_rate", "observed_bad_rate"],
        var_name="measure",
        value_name="rate",
    )
    fairness_fig = px.bar(
        fairness_chart,
        x="segment",
        y="rate",
        color="measure",
        barmode="group",
        color_discrete_map={"approval_rate": GREEN, "observed_bad_rate": RED},
        title="Segment approval and observed bad rates",
        labels={"segment": "Segment", "rate": "Rate", "measure": "Measure"},
    )
    fairness_fig.update_yaxes(tickformat=".0%")
    fairness_fig.update_layout(height=390)
    st.plotly_chart(fairness_fig, width="stretch")

    reasons = data["reasons"]
    application = st.selectbox(
        "Application explanation",
        reasons["application_row"].drop_duplicates().head(50),
    )
    selected_reasons = reasons[reasons["application_row"] == application].copy()
    reason_fig = px.bar(
        selected_reasons.sort_values("pd_impact"),
        x="pd_impact",
        y="feature",
        orientation="h",
        color="direction",
        color_discrete_map={"increases_risk": RED, "reduces_risk": GREEN},
        title=f"Local PD sensitivity | Score {selected_reasons['score_pd'].iloc[0]:.1%}",
        labels={"pd_impact": "Change in PD vs reference", "feature": "Feature"},
    )
    reason_fig.update_xaxes(tickformat=".1%")
    reason_fig.update_layout(height=360, showlegend=False)
    st.plotly_chart(reason_fig, width="stretch")

    st.warning(
        "Demonstration model only. Segment diagnostics and local sensitivities are not "
        "production lending decisions or adverse-action notices."
    )
