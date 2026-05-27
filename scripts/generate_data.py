from pathlib import Path
import random

import pandas as pd
from faker import Faker


# Fixed seeds make the generated CSV files reproducible.
SEED = 42
random.seed(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATA_END_DATE = pd.Timestamp("2026-05-27")


TERRITORY_LOCATIONS = [
    ("T001", "Pune Central", "West", "Maharashtra", "Pune"),
    ("T002", "Mumbai Metro", "West", "Maharashtra", "Mumbai"),
    ("T003", "Nashik North", "West", "Maharashtra", "Nashik"),
    ("T004", "Nagpur Vidarbha", "West", "Maharashtra", "Nagpur"),
    ("T005", "Delhi NCR", "North", "Delhi", "Delhi"),
    ("T006", "Gurgaon Corporate", "North", "Haryana", "Gurgaon"),
    ("T007", "Bengaluru Urban", "South", "Karnataka", "Bengaluru"),
    ("T008", "Hyderabad Central", "South", "Telangana", "Hyderabad"),
    ("T009", "Chennai Metro", "South", "Tamil Nadu", "Chennai"),
    ("T010", "Kolkata East", "East", "West Bengal", "Kolkata"),
    ("T011", "Ahmedabad Gujarat", "West", "Gujarat", "Ahmedabad"),
    ("T012", "Jaipur Rajasthan", "North", "Rajasthan", "Jaipur"),
]

SPECIALTIES = [
    "Cardiologist",
    "Diabetologist",
    "Endocrinologist",
    "Pulmonologist",
    "General Physician",
    "Gastroenterologist",
    "Neurologist",
    "Oncologist",
    "Dermatologist",
    "Orthopedic Surgeon",
]

THERAPY_AREAS = [
    "Cardiology",
    "Diabetes",
    "Respiratory",
    "Gastroenterology",
    "Neurology",
    "Oncology",
    "Dermatology",
    "Pain Management",
]

SPECIALTY_TO_THERAPY = {
    "Cardiologist": "Cardiology",
    "Diabetologist": "Diabetes",
    "Endocrinologist": "Diabetes",
    "Pulmonologist": "Respiratory",
    "General Physician": "Pain Management",
    "Gastroenterologist": "Gastroenterology",
    "Neurologist": "Neurology",
    "Oncologist": "Oncology",
    "Dermatologist": "Dermatology",
    "Orthopedic Surgeon": "Pain Management",
}

PRODUCT_NAMES = [
    "Cardiovance",
    "GlucoRight",
    "RespiraPlus",
    "GastroEase",
    "NeuroCalm",
    "OncoRelief",
    "DermaCure",
    "PainAway",
    "LipidSure",
    "InsuCare",
    "BronchoFree",
    "AcidGuard",
    "MigraLess",
    "Immunex",
    "Skinova",
    "OrthoFlex",
    "BPControl",
    "SugarNorm",
    "AirFlo",
    "HepatoSafe",
    "NervePlus",
    "ChemoCare",
    "Dermashield",
    "JointEase",
    "CardioMax",
]


def random_date(start_date, end_date):
    """Return a random date between two pandas Timestamp values."""
    days_between = (end_date - start_date).days
    return start_date + pd.Timedelta(days=random.randint(0, days_between))


def month_starts(start_date, periods):
    """Return month-start dates for the required number of months."""
    return pd.date_range(start=start_date, periods=periods, freq="MS")


def generate_territories():
    """Create the territory dimension table."""
    rows = []

    for territory_id, territory_name, region, state, city in TERRITORY_LOCATIONS:
        rows.append(
            {
                "territory_id": territory_id,
                "territory_name": territory_name,
                "region": region,
                "state": state,
                "city": city,
                "market_potential": random.randint(8_000_000, 30_000_000),
                "target_hcps": random.randint(35, 60),
            }
        )

    return pd.DataFrame(rows)


def generate_hcps(territories):
    """Create 500 HCPs and assign every HCP to a valid territory."""
    rows = []
    tier_choices = ["Tier 1", "Tier 2", "Tier 3"]
    tier_weights = [0.20, 0.35, 0.45]

    for number in range(1, 501):
        territory = territories.iloc[(number - 1) % len(territories)]
        specialty = random.choice(SPECIALTIES)

        rows.append(
            {
                "hcp_id": f"HCP{number:04d}",
                "hcp_name": f"Dr. {fake.name()}",
                "specialty": specialty,
                "hcp_tier": random.choices(tier_choices, weights=tier_weights, k=1)[0],
                "territory_id": territory["territory_id"],
                "city": territory["city"],
                "state": territory["state"],
                "affiliated_hospital": fake.company() + " Hospital",
                "years_practicing": random.randint(2, 35),
                "patient_volume": random.randint(80, 900),
                "preferred_channel": random.choice(["In-person", "Email", "Phone", "Webinar"]),
                "email_opt_in": random.choice([True, False]),
            }
        )

    return pd.DataFrame(rows)


def generate_medical_reps(territories):
    """Create 40 medical reps and assign each one to a valid territory."""
    rows = []
    managers = [fake.name() for _ in range(8)]

    for number in range(1, 41):
        territory = territories.iloc[(number - 1) % len(territories)]
        experience_years = random.randint(1, 18)

        rows.append(
            {
                "rep_id": f"REP{number:03d}",
                "rep_name": fake.name(),
                "manager_name": random.choice(managers),
                "territory_id": territory["territory_id"],
                "region": territory["region"],
                "hire_date": fake.date_between(
                    start_date=pd.Timestamp("2014-05-27").date(),
                    end_date=pd.Timestamp("2025-11-27").date(),
                ),
                "experience_years": experience_years,
                "monthly_call_target": random.choice([80, 90, 100, 110, 120]),
                "sales_target": random.randint(500_000, 1_800_000),
            }
        )

    return pd.DataFrame(rows)


def generate_products():
    """Create 25 pharma products across common therapy areas."""
    rows = []

    for number, product_name in enumerate(PRODUCT_NAMES, start=1):
        therapy_area = THERAPY_AREAS[(number - 1) % len(THERAPY_AREAS)]

        rows.append(
            {
                "product_id": f"PROD{number:03d}",
                "product_name": product_name,
                "therapy_area": therapy_area,
                "brand_type": random.choice(["Branded", "Generic", "Specialty"]),
                "launch_date": fake.date_between(
                    start_date=pd.Timestamp("2016-05-27").date(),
                    end_date=pd.Timestamp("2025-11-27").date(),
                ),
                "unit_price": round(random.uniform(120, 4500), 2),
                "margin_percent": round(random.uniform(22, 68), 2),
                "target_specialty": random.choice(
                    [
                        specialty
                        for specialty, mapped_area in SPECIALTY_TO_THERAPY.items()
                        if mapped_area == therapy_area
                    ]
                ),
            }
        )

    return pd.DataFrame(rows)


def generate_hcp_calls(hcps, reps, products):
    """Create 18 months of HCP call activity."""
    rows = []
    call_id = 1
    start_date = DATA_END_DATE - pd.DateOffset(months=17)
    end_date = DATA_END_DATE
    hcps_by_territory = {
        territory_id: group.to_dict("records")
        for territory_id, group in hcps.groupby("territory_id")
    }
    products_by_therapy = {
        therapy_area: group.to_dict("records")
        for therapy_area, group in products.groupby("therapy_area")
    }
    all_products = products.to_dict("records")

    for month_start in month_starts(start_date, 18):
        month_end = month_start + pd.offsets.MonthEnd(0)

        for _, rep in reps.iterrows():
            territory_hcps = hcps_by_territory.get(rep["territory_id"], [])
            if not territory_hcps:
                continue

            monthly_call_count = random.randint(20, 35)

            for _ in range(monthly_call_count):
                hcp = random.choice(territory_hcps)
                therapy_area = SPECIALTY_TO_THERAPY[hcp["specialty"]]
                matching_products = products_by_therapy.get(therapy_area, all_products)
                product = random.choice(matching_products)
                call_date = random_date(month_start, month_end)
                call_status = random.choices(
                    ["Completed", "Rescheduled", "Cancelled"],
                    weights=[0.82, 0.12, 0.06],
                    k=1,
                )[0]

                rows.append(
                    {
                        "call_id": f"CALL{call_id:06d}",
                        "call_date": call_date.date(),
                        "hcp_id": hcp["hcp_id"],
                        "rep_id": rep["rep_id"],
                        "territory_id": rep["territory_id"],
                        "product_id": product["product_id"],
                        "call_type": random.choice(["Planned", "Ad hoc", "Follow-up"]),
                        "call_status": call_status,
                        "call_duration_minutes": random.randint(5, 45),
                        "discussion_topic": random.choice(
                            [
                                "New clinical evidence",
                                "Brand reminder",
                                "Patient affordability",
                                "Dose optimization",
                                "Sample follow-up",
                                "Conference invite",
                            ]
                        ),
                        "sample_dropped": random.choice([True, False]),
                        "next_call_planned_date": (
                            call_date + pd.Timedelta(days=random.randint(14, 45))
                        ).date(),
                        "engagement_score": random.randint(1, 100),
                    }
                )
                call_id += 1

    return pd.DataFrame(rows)


def generate_sales(hcps, reps, products):
    """Create HCP-level sales transactions for 18 months."""
    rows = []
    sales_id = 1
    start_date = DATA_END_DATE - pd.DateOffset(months=17)
    hcps_by_territory = {
        territory_id: group.to_dict("records")
        for territory_id, group in hcps.groupby("territory_id")
    }
    products_by_therapy = {
        therapy_area: group.to_dict("records")
        for therapy_area, group in products.groupby("therapy_area")
    }
    all_products = products.to_dict("records")

    for sale_month in month_starts(start_date, 18):
        for _, rep in reps.iterrows():
            territory_hcps = hcps_by_territory.get(rep["territory_id"], [])
            if not territory_hcps:
                continue

            monthly_sales_count = random.randint(18, 32)

            for _ in range(monthly_sales_count):
                hcp = random.choice(territory_hcps)
                therapy_area = SPECIALTY_TO_THERAPY[hcp["specialty"]]
                product_pool = products_by_therapy.get(therapy_area, all_products)
                product = random.choice(product_pool)

                tier_multiplier = {"Tier 1": 1.8, "Tier 2": 1.2, "Tier 3": 0.8}
                base_units = random.randint(8, 80)
                units_sold = int(base_units * tier_multiplier[hcp["hcp_tier"]])
                gross_sales = round(units_sold * product["unit_price"], 2)
                discount_amount = round(gross_sales * random.uniform(0.02, 0.16), 2)
                net_sales = round(gross_sales - discount_amount, 2)
                sale_date = random_date(sale_month, sale_month + pd.offsets.MonthEnd(0))

                rows.append(
                    {
                        "sales_id": f"SALE{sales_id:06d}",
                        "sale_date": sale_date.date(),
                        "sale_month": sale_month.strftime("%Y-%m"),
                        "hcp_id": hcp["hcp_id"],
                        "territory_id": rep["territory_id"],
                        "rep_id": rep["rep_id"],
                        "product_id": product["product_id"],
                        "units_sold": units_sold,
                        "gross_sales": gross_sales,
                        "discount_amount": discount_amount,
                        "net_sales": net_sales,
                        "sales_channel": random.choice(["Retail", "Hospital", "Distributor"]),
                    }
                )
                sales_id += 1

    return pd.DataFrame(rows)


def tune_rep_sales_targets(reps, sales):
    """Set realistic rep targets based on generated rep-level sales."""
    target_rng = random.Random(SEED + 1000)
    rep_sales = sales.groupby("rep_id")["net_sales"].sum().to_dict()
    rep_ids = list(reps["rep_id"])
    target_rng.shuffle(rep_ids)

    # Achievement bands are assigned after sales generation so targets are
    # realistic compared with actual 18-month sales performance.
    achievement_bands = (
        [(70, 90)] * 9
        + [(90, 110)] * 22
        + [(110, 135)] * 7
        + [(140, 160)] * 2
    )

    target_by_rep = {}
    for rep_id, (min_pct, max_pct) in zip(rep_ids, achievement_bands):
        total_net_sales = rep_sales.get(rep_id, 0)
        achievement_pct = target_rng.uniform(min_pct, max_pct)
        sales_target = total_net_sales / (achievement_pct / 100)
        target_by_rep[rep_id] = round(sales_target, 2)

    tuned_reps = reps.copy()
    tuned_reps["sales_target"] = tuned_reps["rep_id"].map(target_by_rep)

    return tuned_reps


def generate_campaigns(territories, products):
    """Create campaigns linked to products and territories."""
    rows = []
    start_date = DATA_END_DATE - pd.DateOffset(months=17)
    end_date = DATA_END_DATE

    for number in range(1, 61):
        territory = territories.iloc[(number - 1) % len(territories)]
        product = products.iloc[(number - 1) % len(products)]
        campaign_start = random_date(start_date, end_date - pd.Timedelta(days=45))
        campaign_end = campaign_start + pd.Timedelta(days=random.randint(30, 120))

        rows.append(
            {
                "campaign_id": f"CAMP{number:04d}",
                "campaign_name": f"{product['product_name']} {random.choice(['Awareness', 'Growth', 'Recall', 'Adoption'])} Campaign",
                "product_id": product["product_id"],
                "territory_id": territory["territory_id"],
                "campaign_type": random.choice(["Email", "Webinar", "Field Event", "Digital Ad"]),
                "start_date": campaign_start.date(),
                "end_date": min(campaign_end, end_date).date(),
                "budget": random.randint(100_000, 1_200_000),
                "target_hcp_tier": random.choice(["Tier 1", "Tier 2", "Tier 3", "All Tiers"]),
                "objective": random.choice(
                    [
                        "Increase brand awareness",
                        "Improve HCP engagement",
                        "Drive product adoption",
                        "Support call planning",
                    ]
                ),
            }
        )

    return pd.DataFrame(rows)


def generate_campaign_engagement(campaigns, hcps, reps):
    """Create engagement events linked to campaigns, HCPs, and reps."""
    rows = []
    engagement_id = 1
    hcps_by_territory = {
        territory_id: group.to_dict("records")
        for territory_id, group in hcps.groupby("territory_id")
    }
    reps_by_territory = {
        territory_id: group.to_dict("records")
        for territory_id, group in reps.groupby("territory_id")
    }

    for _, campaign in campaigns.iterrows():
        territory_hcps = hcps_by_territory.get(campaign["territory_id"], [])
        territory_reps = reps_by_territory.get(campaign["territory_id"], [])

        if not territory_hcps or not territory_reps:
            continue

        if campaign["target_hcp_tier"] != "All Tiers":
            target_hcps = [
                hcp for hcp in territory_hcps if hcp["hcp_tier"] == campaign["target_hcp_tier"]
            ]
            if target_hcps:
                territory_hcps = target_hcps

        engagement_count = random.randint(18, 40)

        for _ in range(engagement_count):
            hcp = random.choice(territory_hcps)
            rep = random.choice(territory_reps)
            engagement_date = random_date(
                pd.Timestamp(campaign["start_date"]),
                pd.Timestamp(campaign["end_date"]),
            )
            opened = random.choices([True, False], weights=[0.72, 0.28], k=1)[0]
            clicked = opened and random.choices([True, False], weights=[0.38, 0.62], k=1)[0]
            attended = random.choices([True, False], weights=[0.24, 0.76], k=1)[0]
            response_score = random.randint(1, 100)

            rows.append(
                {
                    "engagement_id": f"ENG{engagement_id:06d}",
                    "campaign_id": campaign["campaign_id"],
                    "hcp_id": hcp["hcp_id"],
                    "rep_id": rep["rep_id"],
                    "territory_id": campaign["territory_id"],
                    "engagement_date": engagement_date.date(),
                    "channel": random.choice(["Email", "Webinar", "Field Event", "Digital Ad"]),
                    "engagement_type": random.choice(
                        ["Opened Content", "Clicked Link", "Registered", "Attended", "Downloaded"]
                    ),
                    "opened": opened,
                    "clicked": clicked,
                    "attended": attended,
                    "response_score": response_score,
                }
            )
            engagement_id += 1

    return pd.DataFrame(rows)


def save_csv(dataframe, filename):
    """Save a dataframe to data/raw and return the saved row count."""
    output_path = RAW_DATA_DIR / filename
    dataframe.to_csv(output_path, index=False)
    return len(dataframe)


def main():
    """Generate all raw PharmaPulse CSV files."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    territories = generate_territories()
    hcps = generate_hcps(territories)
    medical_reps = generate_medical_reps(territories)
    products = generate_products()
    hcp_calls = generate_hcp_calls(hcps, medical_reps, products)
    sales = generate_sales(hcps, medical_reps, products)
    medical_reps = tune_rep_sales_targets(medical_reps, sales)
    campaigns = generate_campaigns(territories, products)
    campaign_engagement = generate_campaign_engagement(campaigns, hcps, medical_reps)

    csv_outputs = {
        "territories.csv": territories,
        "hcps.csv": hcps,
        "medical_reps.csv": medical_reps,
        "products.csv": products,
        "hcp_calls.csv": hcp_calls,
        "sales.csv": sales,
        "campaigns.csv": campaigns,
        "campaign_engagement.csv": campaign_engagement,
    }

    print("Generated PharmaPulse raw data files:")
    for filename, dataframe in csv_outputs.items():
        row_count = save_csv(dataframe, filename)
        print(f"- {filename}: {row_count:,} rows")


if __name__ == "__main__":
    main()
