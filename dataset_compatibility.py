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
import os


# ============================================================
# SIH26028
# DATASET 1 ↔ DATASET 2 COMPATIBILITY ANALYSIS
# ============================================================


# ============================================================
# DATASET PATHS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"
DATASET2_PATH = "ir_train.csv"


# ============================================================
# START
# ============================================================

print("=" * 80)
print("SIH26028 - DATASET 1 ↔ DATASET 2 COMPATIBILITY ANALYSIS")
print("=" * 80)


# ============================================================
# CHECK FILES
# ============================================================

print("\nChecking dataset files...")

if not os.path.exists(DATASET1_PATH):

    print("❌ Dataset 1 file not found!")
    print("Expected:")
    print(os.path.abspath(DATASET1_PATH))
    exit()

if not os.path.exists(DATASET2_PATH):

    print("❌ Dataset 2 file not found!")
    print("Expected:")
    print(os.path.abspath(DATASET2_PATH))
    exit()

print("✅ Dataset 1 file found")
print("✅ Dataset 2 file found")


# ============================================================
# LOAD DATASET 1
# ============================================================

print("\n" + "=" * 80)
print("LOADING DATASET 1")
print("=" * 80)

df1 = pd.read_csv(DATASET1_PATH)

print("✅ Dataset 1 loaded")
print("Rows:", len(df1))
print("Columns:", len(df1.columns))


# ============================================================
# DATASET 1 COLUMNS
# ============================================================

print("\nDataset 1 columns:")

for i, column in enumerate(df1.columns, start=1):
    print(f"{i:02d}. {column}")


# ============================================================
# LOAD DATASET 2
# ============================================================

print("\n" + "=" * 80)
print("LOADING DATASET 2")
print("=" * 80)

df2 = pd.read_csv(DATASET2_PATH)

print("✅ Dataset 2 loaded")
print("Rows:", len(df2))
print("Columns:", len(df2.columns))


# ============================================================
# DATASET 2 COLUMNS
# ============================================================

print("\nDataset 2 columns:")

for i, column in enumerate(df2.columns, start=1):
    print(f"{i:02d}. {column}")


# ============================================================
# CHECK TRAIN NUMBER COLUMN
# ============================================================

print("\n" + "=" * 80)
print("CHECKING TRAIN NUMBER COLUMNS")
print("=" * 80)

if "train_number" not in df1.columns:

    print("❌ train_number is missing from Dataset 1")
    print("Dataset 1 columns:")
    print(df1.columns.tolist())
    exit()

if "train_number" not in df2.columns:

    print("❌ train_number is missing from Dataset 2")
    print("Dataset 2 columns:")
    print(df2.columns.tolist())
    exit()

print("✅ train_number exists in both datasets")


# ============================================================
# DATASET 1 TRAIN NUMBER FORMAT ANALYSIS
# ============================================================

print("\n" + "=" * 80)
print("DATASET 1 - TRAIN NUMBER FORMAT ANALYSIS")
print("=" * 80)

df1_train_raw = (
    df1["train_number"]
    .dropna()
    .astype(str)
    .str.strip()
)

# Numeric train numbers
df1_numeric_train = df1_train_raw[
    df1_train_raw.str.fullmatch(r"\d+")
]

# Special / non-numeric train numbers
df1_non_numeric_train = df1_train_raw[
    ~df1_train_raw.str.fullmatch(r"\d+")
]

print(
    "Unique numeric train-number values:",
    df1_numeric_train.nunique()
)

print(
    "Unique special/non-numeric train-number values:",
    df1_non_numeric_train.nunique()
)

print(
    "Total unique train-number values:",
    df1_train_raw.nunique()
)


# ============================================================
# SPECIAL TRAIN NUMBERS
# ============================================================

print("\nSpecial/non-numeric train numbers:")

if len(df1_non_numeric_train) == 0:

    print("None found.")

else:

    special_values = sorted(
        df1_non_numeric_train.unique()
    )

    for value in special_values[:100]:
        print(" ", value)

    if len(special_values) > 100:
        print(
            f"... and {len(special_values) - 100} more"
        )


# ============================================================
# CREATE DATASET 1 NUMERIC TRAIN SET
# ============================================================

df1_trains = set(
    df1_numeric_train.astype(int).unique()
)

print(
    "\nNumeric trains used for compatibility:",
    len(df1_trains)
)


# ============================================================
# DATASET 2 TRAIN NUMBERS
# ============================================================

print("\n" + "=" * 80)
print("DATASET 2 - TRAIN NUMBER ANALYSIS")
print("=" * 80)

df2_train_raw = (
    df2["train_number"]
    .dropna()
)

print(
    "Dataset 2 train_number data type:",
    df2["train_number"].dtype
)

print(
    "Unique trains in Dataset 2:",
    df2_train_raw.nunique()
)

df2_trains = set(
    df2_train_raw.astype(int).unique()
)


# ============================================================
# TRAIN NUMBER COMPATIBILITY
# ============================================================

print("\n" + "=" * 80)
print("TRAIN NUMBER COMPATIBILITY")
print("=" * 80)

matched_trains = df1_trains.intersection(
    df2_trains
)

dataset1_only = df1_trains - df2_trains

dataset2_only = df2_trains - df1_trains


print(
    "Dataset 1 numeric trains:",
    len(df1_trains)
)

print(
    "Dataset 2 trains:",
    len(df2_trains)
)

print(
    "Matched trains:",
    len(matched_trains)
)

print(
    "Dataset 1 only:",
    len(dataset1_only)
)

print(
    "Dataset 2 only:",
    len(dataset2_only)
)


# ============================================================
# MATCHING PERCENTAGES
# ============================================================

print("\n" + "=" * 80)
print("MATCHING PERCENTAGES")
print("=" * 80)

if len(df1_trains) > 0:

    dataset1_match_percentage = (
        len(matched_trains)
        / len(df1_trains)
        * 100
    )

else:

    dataset1_match_percentage = 0


if len(df2_trains) > 0:

    dataset2_match_percentage = (
        len(matched_trains)
        / len(df2_trains)
        * 100
    )

else:

    dataset2_match_percentage = 0


print(
    "Dataset 1 coverage by Dataset 2:",
    f"{dataset1_match_percentage:.2f}%"
)

print(
    "Dataset 2 coverage by Dataset 1:",
    f"{dataset2_match_percentage:.2f}%"
)


# ============================================================
# UNMATCHED DATASET 1 TRAINS
# ============================================================

print("\n" + "=" * 80)
print("DATASET 1 TRAINS NOT FOUND IN DATASET 2")
print("=" * 80)

if len(dataset1_only) == 0:

    print("None.")

else:

    for train in sorted(dataset1_only)[:50]:
        print(train)

    if len(dataset1_only) > 50:
        print(
            f"... and {len(dataset1_only) - 50} more"
        )


# ============================================================
# UNMATCHED DATASET 2 TRAINS
# ============================================================

print("\n" + "=" * 80)
print("DATASET 2 TRAINS NOT FOUND IN DATASET 1")
print("=" * 80)

if len(dataset2_only) == 0:

    print("None.")

else:

    for train in sorted(dataset2_only)[:50]:
        print(train)

    if len(dataset2_only) > 50:
        print(
            f"... and {len(dataset2_only) - 50} more"
        )


# ============================================================
# HISTORICAL JOURNEYS PER TRAIN
# ============================================================

print("\n" + "=" * 80)
print("HISTORICAL JOURNEYS PER TRAIN")
print("=" * 80)

journeys_per_train = (
    df2
    .groupby("train_number")
    .size()
    .sort_values(ascending=False)
)

print("\nStatistics:")

print(journeys_per_train.describe())


# ============================================================
# TOP 20 TRAINS
# ============================================================

print("\nTop 20 trains by historical records:")

print(
    journeys_per_train.head(20)
)


# ============================================================
# MATCHED DATASET 2 RECORDS
# ============================================================

print("\n" + "=" * 80)
print("HISTORICAL DATA FOR MATCHED TRAINS")
print("=" * 80)

matched_df2 = df2[
    df2["train_number"].isin(matched_trains)
].copy()

print(
    "Dataset 2 records belonging to matched trains:",
    len(matched_df2)
)


if len(df2) > 0:

    matched_percentage = (
        len(matched_df2)
        / len(df2)
        * 100
    )

else:

    matched_percentage = 0


print(
    "Percentage of Dataset 2 records usable:",
    f"{matched_percentage:.2f}%"
)


# ============================================================
# RECORDS PER MATCHED TRAIN
# ============================================================

print("\n" + "=" * 80)
print("RECORDS PER MATCHED TRAIN")
print("=" * 80)

if len(matched_df2) > 0:

    matched_records_per_train = (
        matched_df2
        .groupby("train_number")
        .size()
    )

    print(
        matched_records_per_train.describe()
    )

else:

    print("No matched trains found.")


# ============================================================
# HISTORICAL FEATURE AVAILABILITY
# ============================================================

print("\n" + "=" * 80)
print("POTENTIAL HISTORICAL FEATURES")
print("=" * 80)

historical_features = [

    "route_historical_ontime_pct",

    "zone_congestion_index",

    "zone_fog_index",

    "season_severity_score",

    "maintenance_score",

    "late_incoming_rake",

    "seat_utilisation_pct",

    "fog_risk_score",

    "distance_km",

    "scheduled_travel_hours"

]


for feature in historical_features:

    if feature in matched_df2.columns:

        print(
            f"✅ {feature:<32} available"
        )

    else:

        print(
            f"❌ {feature:<32} missing"
        )


# ============================================================
# DATASET 1 ↔ DATASET 2 COMMON COLUMNS
# ============================================================

print("\n" + "=" * 80)
print("COMMON COLUMNS")
print("=" * 80)

common_columns = sorted(
    set(df1.columns)
    .intersection(set(df2.columns))
)

print(
    "Number of common columns:",
    len(common_columns)
)

for column in common_columns:
    print(" ", column)


# ============================================================
# CHECK TRAIN NUMBER SAMPLE
# ============================================================

print("\n" + "=" * 80)
print("TRAIN NUMBER SAMPLE")
print("=" * 80)

print("\nDataset 1 numeric train numbers:")

print(
    sorted(df1_trains)[:20]
)

print("\nDataset 2 train numbers:")

print(
    sorted(df2_trains)[:20]
)


# ============================================================
# MATCHED TRAIN SAMPLE
# ============================================================

print("\n" + "=" * 80)
print("MATCHED TRAIN SAMPLE")
print("=" * 80)

if len(matched_trains) > 0:

    print(
        "First 30 matched train numbers:"
    )

    for train in sorted(matched_trains)[:30]:
        print(train)

else:

    print("❌ No matched trains found.")


# ============================================================
# DATE RANGE OF MATCHED DATA
# ============================================================

print("\n" + "=" * 80)
print("MATCHED DATASET 2 DATE RANGE")
print("=" * 80)

if len(matched_df2) > 0:

    matched_df2["departure_date"] = pd.to_datetime(
        matched_df2["departure_date"]
    )

    print(
        "Minimum date:",
        matched_df2["departure_date"].min()
    )

    print(
        "Maximum date:",
        matched_df2["departure_date"].max()
    )

else:

    print("No matched records available.")


# ============================================================
# LEAKAGE CHECK
# ============================================================

print("\n" + "=" * 80)
print("LEAKAGE CHECK")
print("=" * 80)

leakage_columns = [

    "delay_minutes",

    "is_delayed",

    "primary_delay_cause"

]


for column in leakage_columns:

    if column in df2.columns:

        print(
            f"❌ {column:<25} "
            "DO NOT USE AS NORMAL MODEL INPUT"
        )


# ============================================================
# POTENTIAL SAFE FEATURES
# ============================================================

print("\n" + "=" * 80)
print("POTENTIAL SAFE DATASET 2 FEATURES")
print("=" * 80)

safe_features = [

    "train_number",
    "train_type",

    "year",
    "month",
    "day_of_week",
    "departure_hour",

    "is_weekend",
    "is_night_departure",
    "is_peak_hour",
    "is_festival_season",

    "season",

    "zone",
    "zone_abbr",

    "source_station_category",
    "destination_station_category",

    "distance_km",
    "num_scheduled_stops",
    "scheduled_travel_hours",

    "track_doubled",
    "is_hdn_route",

    "traction_type",
    "is_electrified",

    "psr_count",
    "is_circular_route",

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


for feature in safe_features:

    if feature in df2.columns:

        print(
            f"✅ {feature}"
        )

    else:

        print(
            f"❌ {feature} - NOT FOUND"
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("FINAL COMPATIBILITY SUMMARY")
print("=" * 80)

print(
    f"Dataset 1 rows:                 {len(df1):,}"
)

print(
    f"Dataset 1 columns:              {len(df1.columns)}"
)

print(
    f"Dataset 1 numeric trains:       {len(df1_trains):,}"
)

print(
    f"Dataset 1 special train values: "
    f"{df1_non_numeric_train.nunique():,}"
)

print(
    f"Dataset 2 rows:                 {len(df2):,}"
)

print(
    f"Dataset 2 columns:              {len(df2.columns)}"
)

print(
    f"Dataset 2 trains:               {len(df2_trains):,}"
)

print(
    f"Matched trains:                 {len(matched_trains):,}"
)

print(
    f"Dataset 1 coverage:             "
    f"{dataset1_match_percentage:.2f}%"
)

print(
    f"Dataset 2 usable records:       "
    f"{len(matched_df2):,}"
)

print(
    f"Dataset 2 usable coverage:      "
    f"{matched_percentage:.2f}%"
)

print(
    f"Common columns:                 "
    f"{len(common_columns)}"
)

print("\nCompatibility analysis completed successfully! 🚂")


# ============================================================
# END
# ============================================================