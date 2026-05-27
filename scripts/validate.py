from pathlib import Path

import pandas as pd


# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_DATA_DIR = PROJECT_ROOT / "data" / "cleaned"
SAMPLE_OUTPUTS_DIR = PROJECT_ROOT / "data" / "sample_outputs"
REPORT_PATH = SAMPLE_OUTPUTS_DIR / "validation_report.txt"


# Expected project date range for generated calls and sales.
PROJECT_START_DATE = pd.Timestamp("2025-01-01")
PROJECT_END_DATE = pd.Timestamp("2026-06-30")


EXPECTED_COLUMNS = {
    "territories.csv": [
        "territory_id",
        "territory_name",
        "region",
        "state",
        "city",
        "market_potential",
        "target_hcps",
    ],
    "hcps.csv": [
        "hcp_id",
        "hcp_name",
        "specialty",
        "hcp_tier",
        "territory_id",
        "city",
        "state",
        "affiliated_hospital",
        "years_practicing",
        "patient_volume",
        "preferred_channel",
        "email_opt_in",
    ],
    "medical_reps.csv": [
        "rep_id",
        "rep_name",
        "manager_name",
        "territory_id",
        "region",
        "hire_date",
        "experience_years",
        "monthly_call_target",
        "sales_target",
    ],
    "products.csv": [
        "product_id",
        "product_name",
        "therapy_area",
        "brand_type",
        "launch_date",
        "unit_price",
        "margin_percent",
        "target_specialty",
    ],
    "hcp_calls.csv": [
        "call_id",
        "call_date",
        "hcp_id",
        "rep_id",
        "territory_id",
        "product_id",
        "call_type",
        "call_status",
        "call_duration_minutes",
        "discussion_topic",
        "sample_dropped",
        "next_call_planned_date",
        "engagement_score",
    ],
    "sales.csv": [
        "sales_id",
        "sale_date",
        "sale_month",
        "hcp_id",
        "territory_id",
        "rep_id",
        "product_id",
        "units_sold",
        "gross_sales",
        "discount_amount",
        "net_sales",
        "sales_channel",
    ],
    "campaigns.csv": [
        "campaign_id",
        "campaign_name",
        "product_id",
        "territory_id",
        "campaign_type",
        "start_date",
        "end_date",
        "budget",
        "target_hcp_tier",
        "objective",
    ],
    "campaign_engagement.csv": [
        "engagement_id",
        "campaign_id",
        "hcp_id",
        "rep_id",
        "territory_id",
        "engagement_date",
        "channel",
        "engagement_type",
        "opened",
        "clicked",
        "attended",
        "response_score",
    ],
}


PRIMARY_KEYS = {
    "territories.csv": "territory_id",
    "hcps.csv": "hcp_id",
    "medical_reps.csv": "rep_id",
    "products.csv": "product_id",
    "hcp_calls.csv": "call_id",
    "sales.csv": "sales_id",
    "campaigns.csv": "campaign_id",
    "campaign_engagement.csv": "engagement_id",
}


NUMERIC_COLUMNS = {
    "territories.csv": ["market_potential", "target_hcps"],
    "hcps.csv": ["years_practicing", "patient_volume"],
    "medical_reps.csv": ["experience_years", "monthly_call_target", "sales_target"],
    "products.csv": ["unit_price", "margin_percent"],
    "hcp_calls.csv": ["call_duration_minutes", "engagement_score"],
    "sales.csv": ["units_sold", "gross_sales", "discount_amount", "net_sales"],
    "campaigns.csv": ["budget"],
    "campaign_engagement.csv": ["response_score"],
}


def add_result(results, section, check_name, passed, details):
    """Store one validation result without stopping the script."""
    results.append(
        {
            "section": section,
            "check_name": check_name,
            "passed": passed,
            "details": details,
        }
    )


def read_cleaned_files(results):
    """Read all cleaned CSV files that exist."""
    dataframes = {}

    for filename in EXPECTED_COLUMNS:
        file_path = CLEANED_DATA_DIR / filename
        exists = file_path.exists()

        add_result(
            results,
            "Expected Files",
            f"{filename} exists",
            exists,
            "Found file" if exists else f"Missing file: {file_path}",
        )

        if exists:
            dataframes[filename] = pd.read_csv(file_path)

    return dataframes


def validate_required_columns(dataframes, results):
    """Check that each table has the columns required by the project schema."""
    for filename, required_columns in EXPECTED_COLUMNS.items():
        if filename not in dataframes:
            continue

        missing_columns = [
            column for column in required_columns if column not in dataframes[filename].columns
        ]

        add_result(
            results,
            "Required Columns",
            f"{filename} required columns",
            len(missing_columns) == 0,
            "All required columns found"
            if not missing_columns
            else f"Missing columns: {', '.join(missing_columns)}",
        )


def validate_primary_keys(dataframes, results):
    """Check that primary keys are present, non-null, and unique."""
    for filename, primary_key in PRIMARY_KEYS.items():
        if filename not in dataframes or primary_key not in dataframes[filename].columns:
            continue

        dataframe = dataframes[filename]
        missing_count = dataframe[primary_key].isna().sum()
        duplicate_count = dataframe[primary_key].duplicated().sum()

        add_result(
            results,
            "Primary Keys",
            f"{filename}.{primary_key} is unique and not missing",
            missing_count == 0 and duplicate_count == 0,
            f"Missing: {missing_count}, duplicates: {duplicate_count}",
        )


def validate_foreign_key(dataframes, results, child_file, child_column, parent_file, parent_column):
    """Check one foreign-key relationship."""
    if child_file not in dataframes or parent_file not in dataframes:
        return

    child_dataframe = dataframes[child_file]
    parent_dataframe = dataframes[parent_file]

    if child_column not in child_dataframe.columns or parent_column not in parent_dataframe.columns:
        return

    parent_values = set(parent_dataframe[parent_column].dropna())
    invalid_count = (~child_dataframe[child_column].isin(parent_values)).sum()

    add_result(
        results,
        "Foreign Keys",
        f"{child_file}.{child_column} references {parent_file}.{parent_column}",
        invalid_count == 0,
        f"Invalid references: {invalid_count}",
    )


def validate_foreign_keys(dataframes, results):
    """Check relationships between dimension and fact tables."""
    relationships = [
        ("hcps.csv", "territory_id", "territories.csv", "territory_id"),
        ("medical_reps.csv", "territory_id", "territories.csv", "territory_id"),
        ("hcp_calls.csv", "hcp_id", "hcps.csv", "hcp_id"),
        ("hcp_calls.csv", "rep_id", "medical_reps.csv", "rep_id"),
        ("hcp_calls.csv", "territory_id", "territories.csv", "territory_id"),
        ("hcp_calls.csv", "product_id", "products.csv", "product_id"),
        ("sales.csv", "hcp_id", "hcps.csv", "hcp_id"),
        ("sales.csv", "rep_id", "medical_reps.csv", "rep_id"),
        ("sales.csv", "territory_id", "territories.csv", "territory_id"),
        ("sales.csv", "product_id", "products.csv", "product_id"),
        ("campaigns.csv", "product_id", "products.csv", "product_id"),
        ("campaigns.csv", "territory_id", "territories.csv", "territory_id"),
        ("campaign_engagement.csv", "campaign_id", "campaigns.csv", "campaign_id"),
        ("campaign_engagement.csv", "hcp_id", "hcps.csv", "hcp_id"),
        ("campaign_engagement.csv", "rep_id", "medical_reps.csv", "rep_id"),
        ("campaign_engagement.csv", "territory_id", "territories.csv", "territory_id"),
    ]

    for relationship in relationships:
        validate_foreign_key(dataframes, results, *relationship)


def validate_numeric_columns(dataframes, results):
    """Check numeric columns are numeric and non-negative."""
    for filename, numeric_columns in NUMERIC_COLUMNS.items():
        if filename not in dataframes:
            continue

        for column in numeric_columns:
            if column not in dataframes[filename].columns:
                continue

            values = pd.to_numeric(dataframes[filename][column], errors="coerce")
            invalid_numeric_count = values.isna().sum()
            negative_count = (values < 0).sum()

            add_result(
                results,
                "Numeric Fields",
                f"{filename}.{column} is numeric and non-negative",
                invalid_numeric_count == 0 and negative_count == 0,
                f"Invalid numeric values: {invalid_numeric_count}, negative values: {negative_count}",
            )


def validate_tiers_and_scores(dataframes, results):
    """Check allowed HCP tier and score ranges."""
    if "hcps.csv" in dataframes and "hcp_tier" in dataframes["hcps.csv"].columns:
        allowed_tiers = {"Tier 1", "Tier 2", "Tier 3"}
        invalid_tiers = ~dataframes["hcps.csv"]["hcp_tier"].isin(allowed_tiers)
        invalid_count = invalid_tiers.sum()

        add_result(
            results,
            "Business Rules",
            "hcps.csv.hcp_tier uses valid tiers",
            invalid_count == 0,
            f"Invalid tier values: {invalid_count}",
        )

    score_checks = [
        ("hcp_calls.csv", "engagement_score"),
        ("campaign_engagement.csv", "response_score"),
    ]

    for filename, column in score_checks:
        if filename not in dataframes or column not in dataframes[filename].columns:
            continue

        values = pd.to_numeric(dataframes[filename][column], errors="coerce")
        invalid_count = (~values.between(1, 100)).sum()

        add_result(
            results,
            "Business Rules",
            f"{filename}.{column} is between 1 and 100",
            invalid_count == 0,
            f"Out-of-range scores: {invalid_count}",
        )


def validate_campaign_engagement_dates(dataframes, results):
    """Check engagement events occur during their campaign window."""
    if "campaign_engagement.csv" not in dataframes or "campaigns.csv" not in dataframes:
        return

    engagement = dataframes["campaign_engagement.csv"]
    campaigns = dataframes["campaigns.csv"]

    merged = engagement.merge(
        campaigns[["campaign_id", "start_date", "end_date"]],
        on="campaign_id",
        how="left",
    )

    engagement_dates = pd.to_datetime(merged["engagement_date"], errors="coerce")
    start_dates = pd.to_datetime(merged["start_date"], errors="coerce")
    end_dates = pd.to_datetime(merged["end_date"], errors="coerce")
    invalid_count = ((engagement_dates < start_dates) | (engagement_dates > end_dates)).sum()
    missing_date_count = (
        engagement_dates.isna() | start_dates.isna() | end_dates.isna()
    ).sum()

    add_result(
        results,
        "Date Rules",
        "Campaign engagement dates fall within campaign dates",
        invalid_count == 0 and missing_date_count == 0,
        f"Outside campaign window: {invalid_count}, missing dates: {missing_date_count}",
    )


def validate_project_date_range(dataframes, results):
    """Check calls and sales fall within the expected generated project range."""
    date_checks = [
        ("hcp_calls.csv", "call_date"),
        ("sales.csv", "sale_date"),
    ]

    for filename, column in date_checks:
        if filename not in dataframes or column not in dataframes[filename].columns:
            continue

        dates = pd.to_datetime(dataframes[filename][column], errors="coerce")
        invalid_count = (
            dates.isna()
            | (dates < PROJECT_START_DATE)
            | (dates > PROJECT_END_DATE)
        ).sum()

        add_result(
            results,
            "Date Rules",
            f"{filename}.{column} falls within project date range",
            invalid_count == 0,
            f"Outside {PROJECT_START_DATE.date()} to {PROJECT_END_DATE.date()}: {invalid_count}",
        )


def validate_territory_match(
    dataframes,
    results,
    child_file,
    child_id_column,
    child_territory_column,
    parent_file,
    parent_id_column,
    parent_territory_column,
):
    """Check that related records agree on territory_id."""
    if child_file not in dataframes or parent_file not in dataframes:
        return

    child_dataframe = dataframes[child_file]
    parent_dataframe = dataframes[parent_file]
    needed_child_columns = {child_id_column, child_territory_column}
    needed_parent_columns = {parent_id_column, parent_territory_column}

    if not needed_child_columns.issubset(child_dataframe.columns):
        return
    if not needed_parent_columns.issubset(parent_dataframe.columns):
        return

    merged = child_dataframe.merge(
        parent_dataframe[[parent_id_column, parent_territory_column]],
        left_on=child_id_column,
        right_on=parent_id_column,
        how="left",
        suffixes=("_child", "_parent"),
    )

    if child_territory_column == parent_territory_column:
        child_territory_name = f"{child_territory_column}_child"
        parent_territory_name = f"{parent_territory_column}_parent"
    else:
        child_territory_name = child_territory_column
        parent_territory_name = parent_territory_column

    child_territory = merged[child_territory_name]
    parent_territory = merged[parent_territory_name]
    mismatch_count = (child_territory != parent_territory).sum()

    add_result(
        results,
        "Territory Consistency",
        (
            f"{child_file}.{child_territory_column} matches "
            f"{parent_file}.{parent_territory_column}"
        ),
        mismatch_count == 0,
        f"Territory mismatches: {mismatch_count}",
    )


def validate_territory_consistency(dataframes, results):
    """Check territory_id consistency across calls, sales, and campaign engagement."""
    checks = [
        (
            "hcp_calls.csv",
            "hcp_id",
            "territory_id",
            "hcps.csv",
            "hcp_id",
            "territory_id",
        ),
        (
            "hcp_calls.csv",
            "rep_id",
            "territory_id",
            "medical_reps.csv",
            "rep_id",
            "territory_id",
        ),
        (
            "sales.csv",
            "hcp_id",
            "territory_id",
            "hcps.csv",
            "hcp_id",
            "territory_id",
        ),
        (
            "sales.csv",
            "rep_id",
            "territory_id",
            "medical_reps.csv",
            "rep_id",
            "territory_id",
        ),
        (
            "campaign_engagement.csv",
            "campaign_id",
            "territory_id",
            "campaigns.csv",
            "campaign_id",
            "territory_id",
        ),
        (
            "campaign_engagement.csv",
            "hcp_id",
            "territory_id",
            "hcps.csv",
            "hcp_id",
            "territory_id",
        ),
    ]

    for check in checks:
        validate_territory_match(dataframes, results, *check)


def build_report(results):
    """Create a readable text report from validation results."""
    total_checks = len(results)
    passed_checks = sum(result["passed"] for result in results)
    failed_checks = total_checks - passed_checks

    lines = [
        "PharmaPulse Validation Report",
        "=" * 29,
        "",
        f"Total checks: {total_checks}",
        f"Passed checks: {passed_checks}",
        f"Failed checks: {failed_checks}",
        "",
    ]

    current_section = None
    for result in results:
        if result["section"] != current_section:
            current_section = result["section"]
            lines.extend([current_section, "-" * len(current_section)])

        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"[{status}] {result['check_name']}")
        lines.append(f"       {result['details']}")

    return "\n".join(lines) + "\n"


def print_summary(results):
    """Print a short validation summary to the terminal."""
    total_checks = len(results)
    passed_checks = sum(result["passed"] for result in results)
    failed_checks = total_checks - passed_checks

    print("Validation summary:")
    print(f"- Total checks: {total_checks}")
    print(f"- Passed checks: {passed_checks}")
    print(f"- Failed checks: {failed_checks}")
    print(f"- Report saved to: {REPORT_PATH}")

    if failed_checks:
        print("\nFailed checks:")
        for result in results:
            if not result["passed"]:
                print(f"- {result['check_name']}: {result['details']}")


def main():
    """Run all cleaned-data validation checks."""
    SAMPLE_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    dataframes = read_cleaned_files(results)

    validate_required_columns(dataframes, results)
    validate_primary_keys(dataframes, results)
    validate_foreign_keys(dataframes, results)
    validate_numeric_columns(dataframes, results)
    validate_tiers_and_scores(dataframes, results)
    validate_campaign_engagement_dates(dataframes, results)
    validate_project_date_range(dataframes, results)
    validate_territory_consistency(dataframes, results)

    report = build_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print_summary(results)


if __name__ == "__main__":
    main()
