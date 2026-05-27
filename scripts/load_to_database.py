import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_DATA_DIR = PROJECT_ROOT / "data" / "cleaned"
ENV_PATH = PROJECT_ROOT / ".env"


# Load parent tables first, then child tables with foreign keys.
LOAD_ORDER = [
    ("territories", "territories.csv"),
    ("products", "products.csv"),
    ("hcps", "hcps.csv"),
    ("medical_reps", "medical_reps.csv"),
    ("campaigns", "campaigns.csv"),
    ("hcp_calls", "hcp_calls.csv"),
    ("sales", "sales.csv"),
    ("campaign_engagement", "campaign_engagement.csv"),
]


# Truncate child tables first. The same order is used in one TRUNCATE command
# so PostgreSQL can handle foreign-key relationships safely.
TRUNCATE_ORDER = [
    "campaign_engagement",
    "sales",
    "hcp_calls",
    "campaigns",
    "medical_reps",
    "hcps",
    "products",
    "territories",
]


def get_database_url():
    """Build a SQLAlchemy database URL from .env values."""
    load_dotenv(ENV_PATH)

    required_variables = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing_variables = [
        variable for variable in required_variables if not os.getenv(variable)
    ]

    if missing_variables:
        missing_list = ", ".join(missing_variables)
        raise ValueError(f"Missing required .env values: {missing_list}")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )


def check_cleaned_csv_files():
    """Stop before truncating tables if any cleaned CSV file is missing."""
    missing_files = []

    for _, filename in LOAD_ORDER:
        file_path = CLEANED_DATA_DIR / filename
        if not file_path.exists():
            missing_files.append(file_path)

    if missing_files:
        missing_text = "\n".join(f"- {path}" for path in missing_files)
        raise FileNotFoundError(f"Missing cleaned CSV files:\n{missing_text}")


def truncate_tables(connection):
    """Remove existing rows before loading fresh cleaned data."""
    table_list = ", ".join(TRUNCATE_ORDER)
    connection.execute(text(f"TRUNCATE TABLE {table_list};"))


def load_tables(connection):
    """Load each cleaned CSV into its matching PostgreSQL table."""
    loaded_counts = {}

    for table_name, filename in LOAD_ORDER:
        file_path = CLEANED_DATA_DIR / filename
        dataframe = pd.read_csv(file_path)

        print(f"- Loading {table_name} from {filename}: {len(dataframe):,} rows")
        dataframe.to_sql(
            table_name,
            con=connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        loaded_counts[table_name] = len(dataframe)

    return loaded_counts


def verify_table_counts(connection):
    """Query PostgreSQL for actual row counts after loading."""
    database_counts = {}

    for table_name, _ in LOAD_ORDER:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
        database_counts[table_name] = result.scalar_one()

    return database_counts


def print_count_summary(loaded_counts, database_counts):
    """Print loaded CSV row counts next to PostgreSQL row counts."""
    print("\nTable row counts:")

    for table_name, _ in LOAD_ORDER:
        loaded_count = loaded_counts[table_name]
        database_count = database_counts[table_name]
        status = "OK" if loaded_count == database_count else "MISMATCH"
        print(
            f"- {table_name}: loaded {loaded_count:,}, "
            f"database {database_count:,} ({status})"
        )


def main():
    """Load cleaned PharmaPulse CSV files into PostgreSQL."""
    print("Connecting to database...")
    database_url = get_database_url()
    engine = create_engine(database_url)

    print("Checking cleaned CSV files...")
    check_cleaned_csv_files()

    with engine.begin() as connection:
        print("Truncating existing tables...")
        truncate_tables(connection)

        print("Loading each table...")
        loaded_counts = load_tables(connection)

        print("Verifying database row counts...")
        database_counts = verify_table_counts(connection)

    print_count_summary(loaded_counts, database_counts)
    print("\nLoad completed successfully.")


if __name__ == "__main__":
    main()
