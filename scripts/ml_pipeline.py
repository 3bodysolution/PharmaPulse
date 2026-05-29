"""
PharmaPulse ML and analytics pipeline.

This script builds an explainable analytics layer from cleaned CSV inputs.
It produces HCP segmentation, disengagement risk signals, a sales forecast
baseline, next-best-action recommendations, and one master HCP scoring file.
"""

import os
import subprocess
import sys
from pathlib import Path


RANDOM_SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")


try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
except ModuleNotFoundError:
    venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        completed_process = subprocess.run([str(venv_python), *sys.argv], check=False)
        sys.exit(completed_process.returncode)
    raise


FEATURE_COLUMNS = [
    "total_net_sales",
    "total_calls",
    "avg_engagement_score",
    "days_since_last_call",
]


def print_step(message):
    """
    Print a consistent progress message.

    Inputs:
        message: Short text describing the current pipeline step.
    Outputs:
        None. The message is printed to the console.
    """
    print(f"\n--- {message} ---")


def ensure_output_folder(output_dir):
    """
    Create the processed output folder if it does not already exist.

    Inputs:
        output_dir: Path object pointing to the desired output folder.
    Outputs:
        None. The folder is created on disk when needed.
    """
    output_dir.mkdir(parents=True, exist_ok=True)


def load_cleaned_data(cleaned_dir):
    """
    Load cleaned PharmaPulse CSV files used by the ML pipeline.

    Inputs:
        cleaned_dir: Path object pointing to the data/cleaned folder.
    Outputs:
        Dictionary of pandas DataFrames for HCPs, calls, sales, and territories.
    """
    data = {
        "hcps": pd.read_csv(cleaned_dir / "hcps.csv"),
        "hcp_calls": pd.read_csv(cleaned_dir / "hcp_calls.csv"),
        "sales": pd.read_csv(cleaned_dir / "sales.csv"),
        "territories": pd.read_csv(cleaned_dir / "territories.csv"),
    }
    print("Loaded cleaned input files:")
    for name, frame in data.items():
        print(f"  {name}: {len(frame):,} rows")
    return data


def build_hcp_features(hcps, hcp_calls, sales, territories):
    """
    Build one HCP-level feature table from HCP, call, sales, and territory data.

    Inputs:
        hcps: DataFrame containing HCP attributes.
        hcp_calls: DataFrame containing HCP call activity.
        sales: DataFrame containing HCP-level sales records.
        territories: DataFrame containing territory names and attributes.
    Outputs:
        DataFrame with one row per HCP and numeric features for modeling.
    """
    calls = hcp_calls.copy()
    calls["call_date"] = pd.to_datetime(calls["call_date"])
    reference_date = calls["call_date"].max()

    call_summary = (
        calls.groupby("hcp_id", as_index=False)
        .agg(
            total_calls=("call_id", "count"),
            avg_engagement_score=("engagement_score", "mean"),
            last_call_date=("call_date", "max"),
        )
    )
    call_summary["days_since_last_call"] = (
        reference_date - call_summary["last_call_date"]
    ).dt.days

    sales_summary = (
        sales.groupby("hcp_id", as_index=False)
        .agg(total_net_sales=("net_sales", "sum"))
    )

    hcp_features = (
        hcps.merge(
            territories[["territory_id", "territory_name"]],
            on="territory_id",
            how="left",
        )
        .merge(sales_summary, on="hcp_id", how="left")
        .merge(call_summary, on="hcp_id", how="left")
    )

    max_observed_recency = hcp_features["days_since_last_call"].max()
    fill_values = {
        "total_net_sales": 0,
        "total_calls": 0,
        "avg_engagement_score": 0,
        "days_since_last_call": max_observed_recency if pd.notna(max_observed_recency) else 0,
    }
    hcp_features[list(fill_values.keys())] = hcp_features[list(fill_values.keys())].fillna(
        fill_values
    )

    hcp_features["total_calls"] = hcp_features["total_calls"].astype(int)
    hcp_features["avg_engagement_score"] = hcp_features[
        "avg_engagement_score"
    ].round(2)
    hcp_features["days_since_last_call"] = hcp_features[
        "days_since_last_call"
    ].astype(int)
    hcp_features["total_net_sales"] = hcp_features["total_net_sales"].round(2)

    print(f"Dataset latest call_date used as recency reference: {reference_date.date()}")
    print(f"HCP feature table rows: {len(hcp_features):,}")
    return hcp_features


def assign_segment_labels(cluster_profiles):
    """
    Assign readable segment labels after KMeans fitting.

    Inputs:
        cluster_profiles: DataFrame with mean feature values by numeric cluster.
    Outputs:
        Dictionary mapping numeric cluster IDs to readable segment labels.
    """
    high_value_cluster = cluster_profiles["mean_total_net_sales"].idxmax()
    remaining_clusters = [
        cluster_id for cluster_id in cluster_profiles.index if cluster_id != high_value_cluster
    ]
    low_engagement_cluster = (
        cluster_profiles.loc[remaining_clusters]
        .sort_values(["mean_avg_engagement_score", "mean_total_calls"])
        .index[0]
    )
    growth_cluster = [
        cluster_id
        for cluster_id in cluster_profiles.index
        if cluster_id not in {high_value_cluster, low_engagement_cluster}
    ][0]

    return {
        high_value_cluster: "High Value",
        growth_cluster: "Growth Potential",
        low_engagement_cluster: "Low Engagement",
    }


def run_hcp_segmentation(hcp_features, output_dir):
    """
    Run KMeans segmentation on standardized HCP-level features.

    Inputs:
        hcp_features: DataFrame with one row per HCP and model features.
        output_dir: Path object where segmentation outputs should be saved.
    Outputs:
        Tuple containing the HCP segment DataFrame, cluster profile DataFrame,
        and silhouette score.
    """
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(hcp_features[FEATURE_COLUMNS])

    model = KMeans(n_clusters=3, random_state=RANDOM_SEED, n_init=10)
    hcp_segments = hcp_features.copy()
    hcp_segments["cluster_id"] = model.fit_predict(scaled_features)

    score = silhouette_score(scaled_features, hcp_segments["cluster_id"])

    profiles = (
        hcp_segments.groupby("cluster_id")
        .agg(
            mean_total_net_sales=("total_net_sales", "mean"),
            mean_total_calls=("total_calls", "mean"),
            mean_avg_engagement_score=("avg_engagement_score", "mean"),
            mean_days_since_last_call=("days_since_last_call", "mean"),
        )
        .round(2)
    )

    label_map = assign_segment_labels(profiles)
    hcp_segments["segment_label"] = hcp_segments["cluster_id"].map(label_map)
    profiles["segment_label"] = profiles.index.map(label_map)

    cluster_profiles = profiles[
        [
            "segment_label",
            "mean_total_net_sales",
            "mean_total_calls",
            "mean_avg_engagement_score",
            "mean_days_since_last_call",
        ]
    ].reset_index(drop=True)

    hcp_segments_output = hcp_segments[
        [
            "hcp_id",
            "hcp_name",
            "territory_id",
            "territory_name",
            "hcp_tier",
            "total_net_sales",
            "total_calls",
            "avg_engagement_score",
            "days_since_last_call",
            "cluster_id",
            "segment_label",
        ]
    ]

    hcp_segments_output.to_csv(output_dir / "hcp_segments.csv", index=False)
    cluster_profiles.to_csv(output_dir / "cluster_profiles.csv", index=False)

    print(f"Silhouette score: {score:.3f}")
    print("Mean feature values by segment:")
    print(cluster_profiles.to_string(index=False))
    print(f"Saved hcp_segments.csv: {len(hcp_segments_output):,} rows")
    print(f"Saved cluster_profiles.csv: {len(cluster_profiles):,} rows")

    return hcp_segments_output, cluster_profiles, score


def add_percentile_rank(series):
    """
    Convert a numeric pandas Series into percentile ranks on a 0 to 1 scale.

    Inputs:
        series: Numeric pandas Series.
    Outputs:
        Series containing percentile ranks where higher source values rank higher.
    """
    return series.rank(method="average", pct=True).fillna(0)


def min_max_scale(series):
    """
    Scale a numeric pandas Series to the 0 to 1 range.

    Inputs:
        series: Numeric pandas Series.
    Outputs:
        Series scaled between 0 and 1. Constant series are returned as zeros.
    """
    minimum = series.min()
    maximum = series.max()
    if pd.isna(minimum) or pd.isna(maximum) or maximum == minimum:
        return pd.Series(0, index=series.index, dtype=float)
    return (series - minimum) / (maximum - minimum)


def assign_risk_level(row):
    """
    Assign a rule-based HCP disengagement risk level.

    Inputs:
        row: pandas Series containing days_since_last_call and avg_engagement_score.
    Outputs:
        String risk level: High Risk, Medium Risk, or Low Risk.
    """
    days_since_last_call = row["days_since_last_call"]
    avg_engagement_score = row["avg_engagement_score"]

    # Fixed data-driven rules from percentile review:
    # High Risk: days_since_last_call > 19 AND avg_engagement_score < 47.41
    # Medium Risk: days_since_last_call between 9 and 19 OR avg_engagement_score between 47.41 and 50.31
    # Low Risk: all remaining HCPs
    if days_since_last_call > 19 and avg_engagement_score < 47.41:
        return "High Risk"
    if (9 <= days_since_last_call <= 19) or (47.41 <= avg_engagement_score <= 50.31):
        return "Medium Risk"
    return "Low Risk"


def run_churn_risk_scoring(hcp_segments, output_dir):
    """
    Create rule-based HCP disengagement risk scores and levels.

    Inputs:
        hcp_segments: DataFrame containing HCP-level features and segment labels.
        output_dir: Path object where risk scoring output should be saved.
    Outputs:
        DataFrame with HCP risk_level and risk_score.
    """
    risk = hcp_segments.copy()

    print("Reference percentiles used for risk rules:")
    print("  days_since_last_call p25=4, p50=9, p75=19")
    print("  avg_engagement_score p25=47.41, p50=50.31, p75=53.66")

    risk["risk_level"] = risk.apply(assign_risk_level, axis=1)

    recency_risk = min_max_scale(risk["days_since_last_call"])
    low_engagement_risk = 1 - min_max_scale(risk["avg_engagement_score"])
    low_call_activity_signal = 1 - add_percentile_rank(risk["total_calls"])
    low_revenue_signal = 1 - add_percentile_rank(risk["total_net_sales"])

    # Transparent 0-100 risk score:
    # 40% recency risk + 30% low engagement risk + 15% low call activity + 15% low revenue.
    risk["risk_score"] = (
        (
            recency_risk * 0.40
            + low_engagement_risk * 0.30
            + low_call_activity_signal * 0.15
            + low_revenue_signal * 0.15
        )
        * 100
    ).round(1)

    risk_output = risk[
        [
            "hcp_id",
            "hcp_name",
            "territory_id",
            "territory_name",
            "hcp_tier",
            "total_net_sales",
            "total_calls",
            "avg_engagement_score",
            "days_since_last_call",
            "risk_level",
            "risk_score",
        ]
    ]
    risk_output.to_csv(output_dir / "hcp_churn_scores.csv", index=False)

    print("Risk level distribution:")
    print(risk_output["risk_level"].value_counts().to_string())
    print(f"Saved hcp_churn_scores.csv: {len(risk_output):,} rows")
    return risk_output


def build_sales_forecast(sales, output_dir):
    """
    Build a simple monthly sales forecast baseline with a directional range.

    Inputs:
        sales: DataFrame containing sale_date and net_sales.
        output_dir: Path object where the sales forecast output should be saved.
    Outputs:
        DataFrame containing historical monthly revenue and three forecast rows.
    """
    monthly = sales.copy()
    monthly["sale_date"] = pd.to_datetime(monthly["sale_date"])
    monthly["month"] = monthly["sale_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        monthly.groupby("month", as_index=False)
        .agg(actual_revenue=("net_sales", "sum"))
        .sort_values("month")
    )

    last_actual_month = monthly["month"].max()
    recent_average = monthly.tail(3)["actual_revenue"].mean()
    recent_change = monthly["actual_revenue"].diff().tail(3).mean()

    forecast_rows = []
    for step in range(1, 4):
        forecast_month = last_actual_month + pd.DateOffset(months=step)
        forecast_revenue = max(recent_average + recent_change * step, 0)
        forecast_rows.append(
            {
                "month": forecast_month,
                "actual_revenue": np.nan,
                "forecast_revenue": forecast_revenue,
                "forecast_lower": forecast_revenue * 0.90,
                "forecast_upper": forecast_revenue * 1.10,
                "record_type": "Forecast",
            }
        )

    historical = monthly.copy()
    historical["forecast_revenue"] = np.nan
    historical["forecast_lower"] = np.nan
    historical["forecast_upper"] = np.nan
    historical["record_type"] = "Historical"

    forecast = pd.concat([historical, pd.DataFrame(forecast_rows)], ignore_index=True)
    numeric_columns = [
        "actual_revenue",
        "forecast_revenue",
        "forecast_lower",
        "forecast_upper",
    ]
    forecast[numeric_columns] = forecast[numeric_columns].round(2)
    forecast["month"] = forecast["month"].dt.strftime("%Y-%m")
    forecast = forecast[
        [
            "month",
            "actual_revenue",
            "forecast_revenue",
            "forecast_lower",
            "forecast_upper",
            "record_type",
        ]
    ]

    forecast.to_csv(output_dir / "sales_forecast.csv", index=False)

    print("Forecast rows with directional range, not a statistical confidence interval:")
    print(forecast[forecast["record_type"] == "Forecast"].to_string(index=False))
    print(f"Saved sales_forecast.csv: {len(forecast):,} rows")
    return forecast


def recommend_action(row):
    """
    Assign a readable next-best-action recommendation.

    Inputs:
        row: pandas Series containing segment_label, risk_level, recency_score,
             and avg_engagement_score.
    Outputs:
        String recommendation for field planning.
    """
    if row["risk_level"] == "High Risk" or (
        row["segment_label"] == "High Value" and row["recency_score"] >= 0.75
    ):
        return "Schedule follow-up call"
    if row["segment_label"] == "Growth Potential" and row["avg_engagement_score"] >= 50.31:
        return "Review growth opportunity"
    if row["segment_label"] == "High Value" and row["risk_level"] == "Low Risk":
        return "Maintain engagement"
    if row["segment_label"] == "Low Engagement" or row["avg_engagement_score"] < 47.41:
        return "Monitor low engagement"
    return "Maintain engagement"


def build_next_best_action(hcp_segments, risk_scores, output_dir):
    """
    Build next-best-action prioritization scores for HCPs.

    Inputs:
        hcp_segments: DataFrame containing HCP features and segment labels.
        risk_scores: DataFrame containing risk_level and risk_score by HCP.
        output_dir: Path object where next-best-action output should be saved.
    Outputs:
        DataFrame with ranked HCP recommendations.
    """
    nba = hcp_segments.merge(
        risk_scores[["hcp_id", "risk_level", "risk_score"]], on="hcp_id", how="left"
    )

    nba["revenue_percentile_rank"] = add_percentile_rank(nba["total_net_sales"])
    nba["recency_score"] = add_percentile_rank(nba["days_since_last_call"])
    nba["engagement_percentile_rank"] = add_percentile_rank(nba["avg_engagement_score"])
    segment_score_map = {
        "High Value": 1.00,
        "Growth Potential": 0.67,
        "Low Engagement": 0.33,
    }
    nba["segment_score"] = nba["segment_label"].map(segment_score_map).fillna(0.33)

    # prioritization_score =
    #     (revenue_percentile_rank * 0.35)
    #     + (recency_score * 0.30)
    #     + (engagement_percentile_rank * 0.20)
    #     + (segment_score * 0.15)
    nba["prioritization_score"] = (
        (
            nba["revenue_percentile_rank"] * 0.35
            + nba["recency_score"] * 0.30
            + nba["engagement_percentile_rank"] * 0.20
            + nba["segment_score"] * 0.15
        )
        * 100
    ).round(1)

    nba["recommended_action"] = nba.apply(recommend_action, axis=1)
    nba = nba.sort_values(
        ["prioritization_score", "total_net_sales"], ascending=[False, False]
    ).reset_index(drop=True)
    nba["recommendation_rank"] = nba.index + 1

    output_columns = [
        "recommendation_rank",
        "hcp_id",
        "hcp_name",
        "territory_id",
        "territory_name",
        "hcp_tier",
        "total_net_sales",
        "total_calls",
        "avg_engagement_score",
        "days_since_last_call",
        "segment_label",
        "risk_level",
        "risk_score",
        "revenue_percentile_rank",
        "recency_score",
        "engagement_percentile_rank",
        "prioritization_score",
        "recommended_action",
    ]
    nba_output = nba[output_columns]
    nba_output.to_csv(output_dir / "next_best_action.csv", index=False)

    print("Top 5 next-best-action recommendations:")
    print(
        nba_output[
            [
                "recommendation_rank",
                "hcp_id",
                "hcp_name",
                "segment_label",
                "risk_level",
                "prioritization_score",
                "recommended_action",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )
    print(f"Saved next_best_action.csv: {len(nba_output):,} rows")
    return nba_output


def build_hcp_master_scores(hcp_segments, risk_scores, next_best_action, output_dir):
    """
    Build one unified HCP intelligence table for dashboard use.

    Inputs:
        hcp_segments: DataFrame containing HCP features and segment labels.
        risk_scores: DataFrame containing risk_level and risk_score by HCP.
        next_best_action: DataFrame containing prioritization score and action text.
        output_dir: Path object where the master score output should be saved.
    Outputs:
        DataFrame with one row per HCP and all key scoring fields.
    """
    master = (
        hcp_segments.merge(
            risk_scores[["hcp_id", "risk_level", "risk_score"]],
            on="hcp_id",
            how="left",
        )
        .merge(
            next_best_action[
                ["hcp_id", "prioritization_score", "recommended_action"]
            ],
            on="hcp_id",
            how="left",
        )
    )

    master_columns = [
        "hcp_id",
        "hcp_name",
        "territory_id",
        "territory_name",
        "hcp_tier",
        "total_net_sales",
        "total_calls",
        "avg_engagement_score",
        "days_since_last_call",
        "segment_label",
        "risk_level",
        "risk_score",
        "prioritization_score",
        "recommended_action",
    ]
    master = master[master_columns].sort_values("hcp_id").reset_index(drop=True)
    master.to_csv(output_dir / "hcp_master_scores.csv", index=False)

    print(f"Saved hcp_master_scores.csv: {len(master):,} rows")
    return master


def validate_outputs(output_dir):
    """
    Validate that all required ML pipeline outputs were created correctly.

    Inputs:
        output_dir: Path object pointing to the data/processed folder.
    Outputs:
        Dictionary of validation results. Raises AssertionError if any check fails.
    """
    required_files = [
        "hcp_segments.csv",
        "cluster_profiles.csv",
        "hcp_churn_scores.csv",
        "sales_forecast.csv",
        "next_best_action.csv",
        "hcp_master_scores.csv",
    ]
    outputs = {
        file_name: pd.read_csv(output_dir / file_name) for file_name in required_files
    }

    checks = {
        "all_required_files_exist": all((output_dir / file_name).exists() for file_name in required_files),
        "no_missing_hcp_ids_in_segments": outputs["hcp_segments.csv"]["hcp_id"].notna().all(),
        "segment_labels_populated": outputs["hcp_segments.csv"]["segment_label"].notna().all(),
        "cluster_profiles_has_3_rows": len(outputs["cluster_profiles.csv"]) == 3,
        "risk_levels_populated": outputs["hcp_churn_scores.csv"]["risk_level"].notna().all(),
        "forecast_has_historical_rows": (
            outputs["sales_forecast.csv"]["record_type"] == "Historical"
        ).any(),
        "forecast_has_forecast_rows": (
            outputs["sales_forecast.csv"]["record_type"] == "Forecast"
        ).any(),
        "next_best_action_has_recommendations": outputs["next_best_action.csv"][
            "recommended_action"
        ].notna().all(),
        "master_has_500_rows": len(outputs["hcp_master_scores.csv"]) == 500,
        "master_has_unique_hcps": outputs["hcp_master_scores.csv"]["hcp_id"].nunique() == 500,
    }

    failed_checks = [name for name, passed in checks.items() if not passed]
    if failed_checks:
        raise AssertionError(f"Validation failed: {failed_checks}")

    print("Validation checks passed:")
    for name in checks:
        print(f"  {name}: OK")
    return checks


def run_pipeline():
    """
    Run the complete PharmaPulse ML and analytics pipeline.

    Inputs:
        None. The function reads cleaned CSV files from data/cleaned.
    Outputs:
        Dictionary containing key output DataFrames and summary metrics.
    """
    print_step("Starting PharmaPulse ML and analytics pipeline")
    ensure_output_folder(PROCESSED_DIR)

    print_step("Loading cleaned datasets")
    data = load_cleaned_data(CLEANED_DIR)

    print_step("Building HCP-level feature table")
    hcp_features = build_hcp_features(
        data["hcps"], data["hcp_calls"], data["sales"], data["territories"]
    )

    print_step("Component 1: HCP segmentation")
    hcp_segments, cluster_profiles, score = run_hcp_segmentation(
        hcp_features, PROCESSED_DIR
    )

    print_step("Component 2: HCP disengagement risk scoring")
    risk_scores = run_churn_risk_scoring(hcp_segments, PROCESSED_DIR)

    print_step("Component 3: Sales forecast baseline")
    forecast = build_sales_forecast(data["sales"], PROCESSED_DIR)

    print_step("Component 4: Next-best-action scoring")
    next_best_action = build_next_best_action(
        hcp_segments, risk_scores, PROCESSED_DIR
    )

    print_step("Component 5: HCP master scores")
    master = build_hcp_master_scores(
        hcp_segments, risk_scores, next_best_action, PROCESSED_DIR
    )

    print_step("Validating outputs")
    checks = validate_outputs(PROCESSED_DIR)

    print_step("Pipeline completed successfully")
    print("All ML and analytics outputs were created in data/processed.")

    return {
        "hcp_segments": hcp_segments,
        "cluster_profiles": cluster_profiles,
        "silhouette_score": score,
        "risk_scores": risk_scores,
        "forecast": forecast,
        "next_best_action": next_best_action,
        "master": master,
        "validation_checks": checks,
    }


if __name__ == "__main__":
    run_pipeline()
