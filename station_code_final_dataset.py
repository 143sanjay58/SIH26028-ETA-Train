import pandas as pd
import numpy as np

# ============================================================
# STEP 3I
# BUILD FINAL CLEAN ROUTE DATASET
# ============================================================

INPUT_FILE = "ml_ready_segments.csv"
OUTPUT_FILE = "ml_ready_segments_final.csv"


# ============================================================
# VALIDATED STATION CODE MAPPINGS
# ============================================================
# IMPORTANT:
# Original station codes will NOT be changed.
# These mappings are used only to create canonical columns.

MAPPINGS = {
    "SBT": "SBI",
    "CGKR": "CGKP",
    "GOPL": "GDPL",
    "MKI": "BMKI",
    "KWF": "KWAE",
    "BTKL": "BTJL",
    "SRNK": "SRN",
    "CLDY": "CDLD",
}


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("=" * 80)
print("STEP 3I - BUILD FINAL CLEAN ROUTE DATASET")
print("=" * 80)

print("\nLoading Dataset 1...")

df = pd.read_csv(INPUT_FILE)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 2. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "train_number",
    "from_station",
    "from_station_name",
    "to_station",
    "to_station_name",
    "from_arrival",
    "from_departure",
    "to_arrival",
    "to_departure",
    "from_day",
    "to_day",
    "scheduled_run_minutes",
    "status",
]


print("\nChecking required columns...")

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]


if missing_columns:

    print("\nERROR: Required columns are missing:")

    for col in missing_columns:
        print(" -", col)

    raise SystemExit(
        "\nDataset structure is not compatible."
    )


print("All required columns are present.")


# ============================================================
# 3. REMOVE ANY OLD DERIVED COLUMNS
# ============================================================
# This makes the script safe to re-run.

derived_columns = [
    "route_order",
    "from_station_canonical",
    "to_station_canonical",
    "is_overnight",
    "is_long_segment",
    "is_very_long_segment",
    "same_canonical_station",
]


for col in derived_columns:

    if col in df.columns:

        df.drop(
            columns=[col],
            inplace=True
        )


# ============================================================
# 4. PRESERVE ORIGINAL ROUTE ORDER
# ============================================================

print("\nCreating route order...")

df["route_order"] = (
    df.groupby("train_number")
      .cumcount() + 1
)


# ============================================================
# 5. CREATE CANONICAL FROM-STATION CODE
# ============================================================

print("Creating canonical FROM station codes...")

df["from_station_canonical"] = (
    df["from_station"]
    .map(MAPPINGS)
    .fillna(df["from_station"])
)


# ============================================================
# 6. CREATE CANONICAL TO-STATION CODE
# ============================================================

print("Creating canonical TO station codes...")

df["to_station_canonical"] = (
    df["to_station"]
    .map(MAPPINGS)
    .fillna(df["to_station"])
)


# ============================================================
# 7. IDENTIFY OVERNIGHT SEGMENTS
# ============================================================
# A segment is overnight if its destination day is
# greater than its source day.

print("\nIdentifying overnight segments...")

df["is_overnight"] = (
    pd.to_numeric(
        df["to_day"],
        errors="coerce"
    )
    >
    pd.to_numeric(
        df["from_day"],
        errors="coerce"
    )
)


# ============================================================
# 8. IDENTIFY LONG SEGMENTS
# ============================================================

print("Identifying long scheduled segments...")

df["is_long_segment"] = (
    df["scheduled_run_minutes"] >= 180
)


# ============================================================
# 9. IDENTIFY VERY LONG SEGMENTS
# ============================================================

df["is_very_long_segment"] = (
    df["scheduled_run_minutes"] >= 300
)


# ============================================================
# 10. IDENTIFY SAME CANONICAL STATION SEGMENTS
# ============================================================
# IMPORTANT:
# These rows are NOT deleted.
#
# Example:
#
# SBT -> SBI
#
# becomes:
#
# SBI -> SBI
#
# after canonicalization.
#
# We preserve the segment and simply flag it.

print(
    "Checking same-canonical-station segments..."
)

df["same_canonical_station"] = (
    df["from_station_canonical"]
    ==
    df["to_station_canonical"]
)


# ============================================================
# 11. FINAL COLUMN ORDER
# ============================================================

final_columns = [
    "train_number",

    "route_order",

    "from_station",
    "from_station_name",
    "from_station_canonical",

    "to_station",
    "to_station_name",
    "to_station_canonical",

    "from_arrival",
    "from_departure",
    "to_arrival",
    "to_departure",

    "from_day",
    "to_day",

    "scheduled_run_minutes",

    "is_overnight",
    "is_long_segment",
    "is_very_long_segment",
    "same_canonical_station",

    "status",
]


df = df[final_columns]


# ============================================================
# 12. BASIC DATA QUALITY CHECKS
# ============================================================

print("\n" + "=" * 80)
print("FINAL DATA QUALITY CHECKS")
print("=" * 80)


# ------------------------------------------------------------
# Row count
# ------------------------------------------------------------

print(
    "\nTotal rows:",
    len(df)
)


# ------------------------------------------------------------
# Train count
# ------------------------------------------------------------

total_trains = (
    df["train_number"]
    .nunique()
)

print(
    "Unique trains:",
    total_trains
)


# ------------------------------------------------------------
# Duplicate rows
# ------------------------------------------------------------

duplicate_rows = df.duplicated().sum()

print(
    "Duplicate complete rows:",
    duplicate_rows
)


# ------------------------------------------------------------
# Missing values
# ------------------------------------------------------------

missing_values = (
    df.isna()
      .sum()
      .sum()
)

print(
    "Total missing values:",
    missing_values
)


# ============================================================
# 13. STATUS DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("STATUS DISTRIBUTION")
print("=" * 80)

print(
    df["status"]
    .value_counts(dropna=False)
    .to_string()
)


# ============================================================
# 14. OVERNIGHT SEGMENT STATISTICS
# ============================================================

overnight_count = (
    df["is_overnight"]
    .sum()
)

overnight_percentage = (
    overnight_count
    /
    len(df)
    *
    100
)


print("\n" + "=" * 80)
print("OVERNIGHT SEGMENTS")
print("=" * 80)

print(
    "Overnight segments:",
    int(overnight_count)
)

print(
    "Percentage:",
    round(
        overnight_percentage,
        2
    ),
    "%"
)


# ============================================================
# 15. LONG SEGMENT STATISTICS
# ============================================================

long_count = (
    df["is_long_segment"]
    .sum()
)

very_long_count = (
    df["is_very_long_segment"]
    .sum()
)


print("\n" + "=" * 80)
print("LONG SEGMENTS")
print("=" * 80)

print(
    "Segments >= 180 minutes:",
    int(long_count)
)

print(
    "Segments >= 300 minutes:",
    int(very_long_count)
)


# ============================================================
# 16. SAME CANONICAL STATION STATISTICS
# ============================================================

same_canonical_count = (
    df["same_canonical_station"]
    .sum()
)


print("\n" + "=" * 80)
print("SAME CANONICAL STATION SEGMENTS")
print("=" * 80)

print(
    "Same canonical station segments:",
    int(same_canonical_count)
)


if same_canonical_count > 0:

    print("\nSample rows:")

    print(
        df[
            df["same_canonical_station"]
        ][
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_station_name",
                "to_station_name",
                "scheduled_run_minutes",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 17. CANONICAL CODE CHANGE STATISTICS
# ============================================================

from_changed = (
    df["from_station"]
    !=
    df["from_station_canonical"]
).sum()


to_changed = (
    df["to_station"]
    !=
    df["to_station_canonical"]
).sum()


print("\n" + "=" * 80)
print("CANONICAL CODE CHANGES")
print("=" * 80)

print(
    "FROM station codes changed:",
    int(from_changed)
)

print(
    "TO station codes changed:",
    int(to_changed)
)


# ============================================================
# 18. SHOW MAPPING IMPACT
# ============================================================

print("\n" + "=" * 80)
print("STATION CODE MAPPING IMPACT")
print("=" * 80)


mapping_rows = []


for old_code, new_code in MAPPINGS.items():

    from_count = (
        df["from_station"]
        == old_code
    ).sum()

    to_count = (
        df["to_station"]
        == old_code
    ).sum()

    total_count = (
        from_count
        +
        to_count
    )

    mapping_rows.append(
        {
            "old_code": old_code,
            "canonical_code": new_code,
            "from_occurrences": int(from_count),
            "to_occurrences": int(to_count),
            "total_occurrences": int(total_count),
        }
    )


mapping_df = pd.DataFrame(
    mapping_rows
)


print(
    mapping_df.to_string(
        index=False
    )
)


# ============================================================
# 19. VERIFY ORIGINAL CODES WERE PRESERVED
# ============================================================

print("\n" + "=" * 80)
print("ORIGINAL CODE PRESERVATION CHECK")
print("=" * 80)


# Check that canonical columns did not overwrite
# original station-code columns.

original_columns_present = (
    "from_station" in df.columns
    and
    "to_station" in df.columns
)


if original_columns_present:

    print(
        "Original station code columns:",
        "PRESERVED"
    )

else:

    print(
        "ERROR: Original station codes missing!"
    )


# ============================================================
# 20. CHECK SCHEDULED TIME VALUES
# ============================================================

print("\n" + "=" * 80)
print("SCHEDULED TIME CHECK")
print("=" * 80)


negative_times = (
    df["scheduled_run_minutes"]
    < 0
).sum()


zero_times = (
    df["scheduled_run_minutes"]
    == 0
).sum()


print(
    "Negative scheduled times:",
    int(negative_times)
)

print(
    "Zero scheduled times:",
    int(zero_times)
)


# ============================================================
# 21. SAVE FINAL DATASET
# ============================================================

print("\n" + "=" * 80)
print("SAVING FINAL DATASET")
print("=" * 80)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "\nFinal dataset saved as:"
)

print(
    OUTPUT_FILE
)


# ============================================================
# 22. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("FINAL STEP 3I SUMMARY")
print("=" * 80)

print(
    "\nFinal rows:",
    len(df)
)

print(
    "Final trains:",
    total_trains
)

print(
    "Duplicate rows:",
    duplicate_rows
)

print(
    "Missing values:",
    missing_values
)

print(
    "Overnight segments:",
    int(overnight_count)
)

print(
    "Long segments >=180 min:",
    int(long_count)
)

print(
    "Very long segments >=300 min:",
    int(very_long_count)
)

print(
    "Same canonical station segments:",
    int(same_canonical_count)
)

print(
    "FROM codes canonicalized:",
    int(from_changed)
)

print(
    "TO codes canonicalized:",
    int(to_changed)
)


print("\nOutput file:")

print(
    OUTPUT_FILE
)


print(
    "\nOriginal ml_ready_segments.csv was NOT modified."
)


print("\n" + "=" * 80)
print("STEP 3I COMPLETED SUCCESSFULLY")
print("=" * 80)