from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="PharmaPulse Analytics",
    page_icon="💊",
    layout="wide"
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


REQUIRED_FILES = {
    "hcp_master": PROCESSED_DIR / "hcp_master_scores.csv",
    "cluster_profiles": PROCESSED_DIR / "cluster_profiles.csv",
    "risk_scores": PROCESSED_DIR / "hcp_churn_scores.csv",
    "sales_forecast": PROCESSED_DIR / "sales_forecast.csv",
    "next_best_action": PROCESSED_DIR / "next_best_action.csv",
}


ZERO_RESULTS_MESSAGE = "No HCPs match the selected filters. Adjust your selection."


DISPLAY_NAMES = {
    "recommendation_rank": "Rank",
    "hcp_id": "HCP ID",
    "hcp_name": "HCP Name",
    "territory_id": "Territory ID",
    "territory_name": "Territory",
    "hcp_tier": "HCP Tier",
    "total_net_sales": "Total Net Sales",
    "total_calls": "Total Calls",
    "avg_engagement_score": "Engagement Score",
    "days_since_last_call": "Days Since Last Call",
    "segment_label": "Segment",
    "risk_level": "Risk Level",
    "risk_score": "Risk Score",
    "prioritization_score": "Priority Score",
    "recommended_action": "Recommended Action",
    "forecast_revenue": "Forecast Revenue",
    "forecast_lower": "Forecast Lower Range",
    "forecast_upper": "Forecast Upper Range",
    "actual_revenue": "Actual Revenue",
    "record_type": "Record Type",
    "month": "Month",
    "mean_total_net_sales": "Mean Total Net Sales",
    "mean_total_calls": "Mean Total Calls",
    "mean_avg_engagement_score": "Mean Engagement Score",
    "mean_days_since_last_call": "Mean Days Since Last Call",
    "hcp_count": "HCP Count",
}


CURRENCY_COLUMNS = {
    "total_net_sales",
    "forecast_revenue",
    "forecast_lower",
    "forecast_upper",
    "actual_revenue",
    "mean_total_net_sales",
}


SCORE_COLUMNS = {
    "avg_engagement_score",
    "risk_score",
    "prioritization_score",
    "mean_avg_engagement_score",
}


@st.cache_data
def load_csv(path):
    """Load one CSV file and cache it for faster Streamlit reruns."""
    return pd.read_csv(path)


@st.cache_data
def load_app_data(file_map):
    """Load all required processed CSV files for the Streamlit app."""
    return {name: load_csv(path) for name, path in file_map.items()}


def show_missing_file_errors(file_map):
    """Show graceful error messages for missing required input files."""
    missing_files = [path for path in file_map.values() if not path.exists()]
    if not missing_files:
        return

    st.error("Required processed data files are missing.")
    st.write("Run `python scripts/ml_pipeline.py` to generate the processed outputs.")
    for path in missing_files:
        st.write(f"- `{path.relative_to(PROJECT_ROOT)}`")
    st.stop()


def format_inr(value):
    """Format a numeric value as INR using compact M/K notation."""
    if pd.isna(value):
        return "INR 0"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"₹{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"₹{value / 1_000:.1f}K"
    return f"₹{value:,.0f}"


def format_inr_full(value):
    """Format a numeric value as INR with comma separators for tables."""
    if pd.isna(value):
        return ""
    return f"₹{float(value):,.0f}"


def format_score(value):
    """Format engagement, risk, and priority score values for display tables."""
    if pd.isna(value):
        return ""
    return f"{float(value):.1f}"


def format_display_table(data, columns=None):
    """Select, format, and rename columns before rendering a user-facing table."""
    if columns is None:
        display = data.copy()
    else:
        available_columns = [column for column in columns if column in data.columns]
        display = data[available_columns].copy()

    for column in display.columns:
        if column in CURRENCY_COLUMNS:
            display[column] = display[column].apply(format_inr_full)
        elif column in SCORE_COLUMNS:
            display[column] = display[column].apply(format_score)

    return display.rename(columns=DISPLAY_NAMES)


def add_all_filter(label, values):
    """Create a multiselect filter with all values selected by default."""
    clean_values = sorted(pd.Series(values).dropna().unique().tolist())
    return st.multiselect(label, clean_values, default=clean_values)


def filter_hcp_data(data, territory=None, tier=None, segment=None, risk=None, action=None):
    """Apply common HCP filters and return the filtered DataFrame."""
    filtered = data.copy()
    if territory is not None:
        filtered = filtered[filtered["territory_name"].isin(territory)]
    if tier is not None:
        filtered = filtered[filtered["hcp_tier"].isin(tier)]
    if segment is not None:
        filtered = filtered[filtered["segment_label"].isin(segment)]
    if risk is not None:
        filtered = filtered[filtered["risk_level"].isin(risk)]
    if action is not None:
        filtered = filtered[filtered["recommended_action"].isin(action)]
    return filtered


def show_zero_results_warning(data):
    """Return True and show a warning when a filtered HCP DataFrame is empty."""
    if len(data) == 0:
        st.warning(ZERO_RESULTS_MESSAGE)
        return True
    return False


def prepare_display_table(data, columns):
    """Return a display table with only available requested columns."""
    return format_display_table(data, columns)


def render_sidebar():
    """Render sidebar branding and page navigation."""
    st.sidebar.title("PharmaPulse")
    st.sidebar.caption("HCP Engagement & Sales Intelligence")
    st.sidebar.divider()
    return st.sidebar.selectbox(
        "Navigate",
        [
            "Executive Overview",
            "HCP Segments",
            "Risk Monitoring",
            "Next-Best Action",
            "Sales Forecast",
            "HCP Master Table",
        ],
    )


def render_executive_overview(master, forecast):
    """Render executive KPIs and summary charts."""
    st.title("Executive Overview")
    st.caption("A high-level view of HCP reach, revenue, engagement quality, risk, and field prioritization.")

    total_hcps = master["hcp_id"].nunique()
    total_net_sales = master["total_net_sales"].sum()
    avg_engagement = master["avg_engagement_score"].mean()
    high_risk_count = (master["risk_level"] == "High Risk").sum()
    avg_priority = master["prioritization_score"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total HCPs", f"{total_hcps:,}")
    col2.metric("Total Net Sales", format_inr(total_net_sales))
    col3.metric("Average Engagement Score", f"{avg_engagement:.1f}")
    col4.metric("High-Risk HCPs", f"{high_risk_count:,}")
    col5.metric("Average Priority Score", f"{avg_priority:.1f}")

    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("HCP Count by Segment")
        segment_counts = master["segment_label"].value_counts().rename_axis("Segment").reset_index(name="HCP Count")
        if show_zero_results_warning(segment_counts):
            return
        st.bar_chart(segment_counts, x="Segment", y="HCP Count")

    with right:
        st.subheader("HCP Count by Risk Level")
        risk_counts = master["risk_level"].value_counts().rename_axis("Risk Level").reset_index(name="HCP Count")
        if show_zero_results_warning(risk_counts):
            return
        st.bar_chart(risk_counts, x="Risk Level", y="HCP Count")

    st.subheader("Top 10 Territories by Total Net Sales")
    territory_sales = (
        master.groupby("territory_name", as_index=False)
        .agg(total_net_sales=("total_net_sales", "sum"))
        .sort_values("total_net_sales", ascending=False)
        .head(10)
        .rename(columns=DISPLAY_NAMES)
    )
    if not show_zero_results_warning(territory_sales):
        st.bar_chart(territory_sales, x="Territory", y="Total Net Sales")

    with st.expander("Sales forecast preview"):
        st.dataframe(format_display_table(forecast.tail(6)), width="stretch")


def render_hcp_segments(master, cluster_profiles):
    """Render HCP segmentation filters, charts, and cluster profile table."""
    st.title("HCP Segments")
    st.caption("Compare HCP groups by value, call activity, engagement, and call recency signals.")

    col1, col2, col3 = st.columns(3)
    with col1:
        territories = add_all_filter("Territory", master["territory_name"])
    with col2:
        tiers = add_all_filter("HCP Tier", master["hcp_tier"])
    with col3:
        segments = add_all_filter("Segment", master["segment_label"])

    filtered = filter_hcp_data(master, territory=territories, tier=tiers, segment=segments)
    if show_zero_results_warning(filtered):
        return

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Segment Distribution")
        segment_counts = filtered["segment_label"].value_counts().rename_axis("Segment").reset_index(name="HCP Count")
        if not show_zero_results_warning(segment_counts):
            st.bar_chart(segment_counts, x="Segment", y="HCP Count")

    with right:
        st.subheader("Cluster Profiles")
        st.dataframe(format_display_table(cluster_profiles), width="stretch")

    st.subheader("Engagement vs Net Sales")
    fig = go.Figure()
    max_calls = max(filtered["total_calls"].max(), 1)
    for segment_name, segment_data in filtered.groupby("segment_label"):
        marker_size = 8 + (segment_data["total_calls"] / max_calls * 24)
        fig.add_trace(
            go.Scatter(
                x=segment_data["avg_engagement_score"],
                y=segment_data["total_net_sales"],
                mode="markers",
                name=segment_name,
                text=segment_data["hcp_name"],
                marker={"size": marker_size, "sizemode": "diameter", "opacity": 0.75},
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Avg engagement: %{x:.1f}<br>"
                    "Net sales: ₹%{y:,.0f}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        xaxis_title="Average Engagement Score",
        yaxis_title="Total Net Sales",
        legend_title="Segment",
        height=520,
    )
    st.plotly_chart(fig, width="stretch")


def render_risk_monitoring(risk_scores):
    """Render HCP risk monitoring KPIs, chart, and high-risk table."""
    st.title("Risk Monitoring")
    st.caption("Track HCP disengagement risk signals to support timely field follow-up.")

    high_count = (risk_scores["risk_level"] == "High Risk").sum()
    medium_count = (risk_scores["risk_level"] == "Medium Risk").sum()
    low_count = (risk_scores["risk_level"] == "Low Risk").sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("High Risk HCPs", f"{high_count:,}")
    col2.metric("Medium Risk HCPs", f"{medium_count:,}")
    col3.metric("Low Risk HCPs", f"{low_count:,}")

    st.subheader("Risk Level Counts")
    risk_counts = risk_scores["risk_level"].value_counts().rename_axis("Risk Level").reset_index(name="HCP Count")
    if not show_zero_results_warning(risk_counts):
        st.bar_chart(risk_counts, x="Risk Level", y="HCP Count")

    st.subheader("High-Risk HCPs")
    high_risk = risk_scores[risk_scores["risk_level"] == "High Risk"].sort_values("risk_score", ascending=False)
    if show_zero_results_warning(high_risk):
        return
    table_columns = [
        "hcp_id",
        "hcp_name",
        "territory_name",
        "hcp_tier",
        "total_net_sales",
        "avg_engagement_score",
        "days_since_last_call",
        "risk_score",
        "risk_level",
    ]
    st.dataframe(prepare_display_table(high_risk, table_columns), width="stretch")


def render_next_best_action(next_best_action):
    """Render filtered next-best-action recommendations."""
    st.title("Next-Best Action")
    st.caption("Prioritize HCP follow-up using revenue, engagement, recency, segment, and risk signals.")

    col1, col2, col3 = st.columns(3)
    with col1:
        territories = add_all_filter("Territory", next_best_action["territory_name"])
    with col2:
        tiers = add_all_filter("HCP Tier", next_best_action["hcp_tier"])
    with col3:
        segments = add_all_filter("Segment", next_best_action["segment_label"])

    col4, col5 = st.columns(2)
    with col4:
        risks = add_all_filter("Risk Level", next_best_action["risk_level"])
    with col5:
        actions = add_all_filter("Recommended Action", next_best_action["recommended_action"])

    top_n = st.slider("Number of recommendations to show", 10, 50, 20)

    filtered = filter_hcp_data(
        next_best_action,
        territory=territories,
        tier=tiers,
        segment=segments,
        risk=risks,
        action=actions,
    )
    if show_zero_results_warning(filtered):
        return

    filtered = filtered.sort_values("prioritization_score", ascending=False).head(top_n)
    table_columns = [
        "hcp_id",
        "hcp_name",
        "territory_name",
        "hcp_tier",
        "segment_label",
        "risk_level",
        "prioritization_score",
        "recommended_action",
    ]
    st.dataframe(prepare_display_table(filtered, table_columns), width="stretch")


def render_sales_forecast(forecast):
    """Render actual revenue, forecast baseline, and directional forecast range."""
    st.title("Sales Forecast")
    st.caption("Review a simple monthly revenue forecast baseline with a directional planning range.")

    chart_data = forecast.copy()
    chart_data["month"] = pd.to_datetime(chart_data["month"])
    historical = chart_data[chart_data["record_type"] == "Historical"]
    forecast_rows = chart_data[chart_data["record_type"] == "Forecast"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=historical["month"],
            y=historical["actual_revenue"],
            mode="lines+markers",
            name="Actual revenue",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_rows["month"],
            y=forecast_rows["forecast_lower"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            name="Forecast lower",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_rows["month"],
            y=forecast_rows["forecast_upper"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(31, 119, 180, 0.18)",
            line={"width": 0},
            name="Directional range",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_rows["month"],
            y=forecast_rows["forecast_revenue"],
            mode="lines+markers",
            name="Forecast revenue",
        )
    )
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue",
        hovermode="x unified",
        height=520,
    )
    st.plotly_chart(fig, width="stretch")
    st.info("Forecast range is a directional planning range, not a statistical confidence interval.")

    st.subheader("Forecast Table")
    if not show_zero_results_warning(forecast):
        st.dataframe(format_display_table(forecast), width="stretch")


def render_hcp_master_table(master):
    """Render searchable HCP master table with CSV download."""
    st.title("HCP Master Table")
    st.caption("Search, filter, and export the unified HCP intelligence table for planning workflows.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        territories = add_all_filter("Territory", master["territory_name"])
    with col2:
        tiers = add_all_filter("HCP Tier", master["hcp_tier"])
    with col3:
        segments = add_all_filter("Segment", master["segment_label"])
    with col4:
        risks = add_all_filter("Risk Level", master["risk_level"])

    search_text = st.text_input("Search by HCP name")

    filtered = filter_hcp_data(master, territory=territories, tier=tiers, segment=segments, risk=risks)
    if search_text:
        filtered = filtered[filtered["hcp_name"].str.contains(search_text, case=False, na=False)]

    if show_zero_results_warning(filtered):
        return

    display_table = format_display_table(filtered)
    st.dataframe(display_table, width="stretch")
    st.download_button(
        "Download filtered data as CSV",
        data=display_table.to_csv(index=False).encode("utf-8"),
        file_name="pharmapulse_hcp_master_filtered.csv",
        mime="text/csv",
    )


def main():
    """Run the PharmaPulse Streamlit app."""
    show_missing_file_errors(REQUIRED_FILES)
    data = load_app_data(REQUIRED_FILES)

    selected_page = render_sidebar()

    if selected_page == "Executive Overview":
        render_executive_overview(data["hcp_master"], data["sales_forecast"])
    elif selected_page == "HCP Segments":
        render_hcp_segments(data["hcp_master"], data["cluster_profiles"])
    elif selected_page == "Risk Monitoring":
        render_risk_monitoring(data["risk_scores"])
    elif selected_page == "Next-Best Action":
        render_next_best_action(data["next_best_action"])
    elif selected_page == "Sales Forecast":
        render_sales_forecast(data["sales_forecast"])
    elif selected_page == "HCP Master Table":
        render_hcp_master_table(data["hcp_master"])


if __name__ == "__main__":
    main()
