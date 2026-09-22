# WINDOWS_CONSOLE_UTF8_FIX
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd

# ============================================================
# FILE PATHS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"
DATASET2_PATH = "ir_train.csv"


# ============================================================
# LOAD DATABASES
# ============================================================

print("Loading Database 1...")
db1 = pd.read_csv(DATASET1_PATH)

print("Loading Database 2...")
db2 = pd.read_csv(DATASET2_PATH)

print("✅ Both databases loaded!")


# ============================================================
# GET TRAIN NUMBER
# ============================================================

train_number = input("\nEnter train number: ").strip()

print("\n" + "=" * 80)
print("STEP 2 - TRAIN RELATIONSHIP ANALYSIS")
print("=" * 80)

print("Train number:", train_number)


# ============================================================
# DATABASE 1 - ROUTE
# ============================================================

db1_train = db1[
    db1["train_number"].astype(str).str.strip() == train_number
].copy()

print("\n" + "=" * 80)
print("DATABASE 1 - ROUTE")
print("=" * 80)

if len(db1_train) == 0:

    print("❌ Train not found in Database 1")
    exit()

print("✅ Train found")
print("Total route segments:", len(db1_train))

print("\nRoute:")

for _, row in db1_train.iterrows():

    print(
        f"{row['from_station']} ({row['from_station_name']})"
        f" → "
        f"{row['to_station']} ({row['to_station_name']})"
        f" | Scheduled: "
        f"{row['scheduled_run_minutes']} min"
        f" | Day: {row['from_day']} → {row['to_day']}"
    )


# ============================================================
# DATABASE 2 - HISTORICAL JOURNEYS
# ============================================================

db2_train = db2[
    db2["train_number"].astype(str).str.strip() == train_number
].copy()

print("\n" + "=" * 80)
print("DATABASE 2 - HISTORICAL JOURNEYS")
print("=" * 80)

if len(db2_train) == 0:

    print("❌ Train not found in Database 2")
    exit()

print("✅ Train found")
print("Total historical journeys:", len(db2_train))


# ============================================================
# SHOW JOURNEY LIST
# ============================================================

print("\nHistorical journeys:")

journey_columns = [
    "journey_id",
    "departure_date",
    "year",
    "month",
    "season",
    "train_type",
    "zone",
    "distance_km",
    "scheduled_travel_hours",
    "route_historical_ontime_pct"
]

available_columns = [
    column
    for column in journey_columns
    if column in db2_train.columns
]

print(
    db2_train[available_columns]
    .head(20)
    .to_string(index=False)
)


# ============================================================
# SELECT ONE JOURNEY
# ============================================================

selected_journey_id = db2_train.iloc[0]["journey_id"]

journey = db2_train[
    db2_train["journey_id"] == selected_journey_id
].iloc[0]


print("\n" + "=" * 80)
print("SELECTED HISTORICAL JOURNEY")
print("=" * 80)

print("Journey ID:", journey["journey_id"])
print("Train number:", journey["train_number"])
print("Date:", journey["departure_date"])
print("Train type:", journey["train_type"])

print("\nRoute-level information:")
print("Distance:", journey["distance_km"], "km")
print(
    "Scheduled travel:",
    journey["scheduled_travel_hours"],
    "hours"
)

print(
    "Historical on-time percentage:",
    journey["route_historical_ontime_pct"]
)


# ============================================================
# CONTEXT FEATURES
# ============================================================

print("\n" + "=" * 80)
print("HISTORICAL CONTEXT")
print("=" * 80)

context_features = [
    "year",
    "month",
    "day_of_week",
    "departure_hour",
    "is_weekend",
    "is_night_departure",
    "is_peak_hour",
    "is_festival_season",
    "season",
    "track_doubled",
    "is_hdn_route",
    "traction_type",
    "is_electrified",
    "psr_count",
    "is_monsoon_season",
    "is_fog_risk",
    "fog_risk_score",
    "zone_fog_index",
    "zone_congestion_index",
    "season_severity_score",
    "loco_age_years",
    "coach_age_years",
    "has_lhb_coaches",
    "is_rake_shared",
    "maintenance_score",
    "seat_utilisation_pct",
    "is_overloaded",
    "late_incoming_rake",
    "is_special_train",
    "route_historical_ontime_pct"
]

for feature in context_features:

    if feature in journey.index:

        print(
            f"{feature:<35}: {journey[feature]}"
        )


# ============================================================
# LEAKAGE FIELDS - DISPLAY ONLY
# ============================================================

print("\n" + "=" * 80)
print("OUTCOME FIELDS - DO NOT USE AS MODEL INPUT")
print("=" * 80)

outcome_fields = [
    "primary_delay_cause",
    "delay_minutes",
    "is_delayed"
]

for feature in outcome_fields:

    if feature in journey.index:

        print(
            f"{feature:<35}: {journey[feature]}"
        )


# ============================================================
# RELATIONSHIP SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("DATABASE RELATIONSHIP")
print("=" * 80)

print("Database 1 key :", train_number)
print("Database 2 key :", journey["train_number"])

print("\nDatabase 1 provides:")
print("- Station-to-station route")
print("- Scheduled travel time")

print("\nDatabase 2 provides:")
print("- Historical journey")
print("- Date/time context")
print("- Route characteristics")
print("- Weather/risk indicators")
print("- Congestion indicators")
print("- Operational characteristics")

print("\nRelationship:")
print(
    "Database 1.train_number = Database 2.train_number"
)

print("\n✅ STEP 2 COMPLETED")