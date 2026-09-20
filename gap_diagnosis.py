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
# STEP 3B - GAP DIAGNOSIS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"


print("=" * 80)
print("STEP 3B - DISCONNECTED ROUTE GAP DIAGNOSIS")
print("=" * 80)


# ============================================================
# 1. CHECK FILE
# ============================================================

if not os.path.exists(DATASET1_PATH):
    print("\n❌ Dataset 1 not found!")
    print("Expected:")
    print(os.path.abspath(DATASET1_PATH))
    raise SystemExit


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("✅ Dataset loaded")

print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 3. PRESERVE ROUTE ORDER
# ============================================================

df["route_order"] = (
    df.groupby("train_number")
    .cumcount() + 1
)


# ============================================================
# 4. PREVIOUS SEGMENT INFORMATION
# ============================================================

df["previous_to_station"] = (
    df.groupby("train_number")["to_station"]
    .shift(1)
)

df["previous_to_station_name"] = (
    df.groupby("train_number")["to_station_name"]
    .shift(1)
)

df["previous_to_day"] = (
    df.groupby("train_number")["to_day"]
    .shift(1)
)

df["previous_run_minutes"] = (
    df.groupby("train_number")[
        "scheduled_run_minutes"
    ].shift(1)
)


# ============================================================
# 5. IDENTIFY DISCONNECTED LINKS
# ============================================================

df["is_first_segment"] = (
    df["previous_to_station"].isna()
)

df["is_continuous"] = (
    df["is_first_segment"]
    |
    (
        df["previous_to_station"]
        ==
        df["from_station"]
    )
)


gaps = df[
    (~df["is_first_segment"])
    &
    (~df["is_continuous"])
].copy()


print("\n" + "=" * 80)
print("GAP OVERVIEW")
print("=" * 80)

print(
    "Total disconnected links:",
    len(gaps)
)


# ============================================================
# 6. GAP SIZE / ROUTE ORDER
# ============================================================

# Since each retained segment has an order,
# consecutive retained segments indicate where
# a possible timetable portion is missing.

gaps["route_order_difference"] = 1


print("\nRoute-order gaps calculated.")


# ============================================================
# 7. SAME STATION NAME / CODE CHECK
# ============================================================

gaps["same_station_code"] = (
    gaps["previous_to_station"]
    ==
    gaps["from_station"]
)

gaps["same_station_name"] = (
    gaps["previous_to_station_name"]
    ==
    gaps["from_station_name"]
)


# ============================================================
# 8. TIMING INFORMATION
# ============================================================

# Difference between the previous segment's destination
# and the current segment's origin.
#
# This is useful for identifying large timetable gaps.

gaps["previous_to_day"] = pd.to_numeric(
    gaps["previous_to_day"],
    errors="coerce"
)

gaps["from_day_numeric"] = pd.to_numeric(
    gaps["from_day"],
    errors="coerce"
)


gaps["day_difference"] = (
    gaps["from_day_numeric"]
    -
    gaps["previous_to_day"]
)


# ============================================================
# 9. CLASSIFY GAP TYPE
# ============================================================

def classify_gap(row):

    previous_station = str(
        row["previous_to_station"]
    ).strip()

    current_station = str(
        row["from_station"]
    ).strip()

    previous_name = str(
        row["previous_to_station_name"]
    ).strip().upper()

    current_name = str(
        row["from_station_name"]
    ).strip().upper()

    # Exact station code mismatch
    if previous_station != current_station:

        # Same station name but different code
        if (
            previous_name == current_name
            and previous_name != "NAN"
        ):
            return "possible_code_variation"

        return "route_gap"

    return "other"


gaps["gap_type"] = gaps.apply(
    classify_gap,
    axis=1
)


# ============================================================
# 10. GAP TYPE DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("GAP TYPE DISTRIBUTION")
print("=" * 80)

print(
    gaps["gap_type"]
    .value_counts()
)


# ============================================================
# 11. MOST COMMON GAP PAIRS
# ============================================================

print("\n" + "=" * 80)
print("MOST COMMON DISCONNECTED STATION PAIRS")
print("=" * 80)


gap_pairs = (
    gaps.groupby(
        [
            "previous_to_station",
            "from_station"
        ]
    )
    .size()
    .reset_index(
        name="gap_count"
    )
    .sort_values(
        "gap_count",
        ascending=False
    )
)


print(
    gap_pairs.head(30)
    .to_string(index=False)
)


# ============================================================
# 12. MOST AFFECTED TRAINS
# ============================================================

print("\n" + "=" * 80)
print("MOST AFFECTED TRAINS")
print("=" * 80)


train_gap_counts = (
    gaps.groupby("train_number")
    .size()
    .reset_index(
        name="gap_count"
    )
    .sort_values(
        "gap_count",
        ascending=False
    )
)


print(
    train_gap_counts.head(30)
    .to_string(index=False)
)


# ============================================================
# 13. GAP COUNT PER TRAIN + CONTINUITY
# ============================================================

train_total = (
    df.groupby("train_number")
    .size()
    .reset_index(
        name="total_segments"
    )
)


train_gap_analysis = train_total.merge(
    train_gap_counts,
    on="train_number",
    how="left"
)


train_gap_analysis["gap_count"] = (
    train_gap_analysis["gap_count"]
    .fillna(0)
    .astype(int)
)


train_gap_analysis["links_checked"] = (
    train_gap_analysis["total_segments"] - 1
)


train_gap_analysis["continuity_percentage"] = 100.0


mask = (
    train_gap_analysis["links_checked"] > 0
)


train_gap_analysis.loc[
    mask,
    "continuity_percentage"
] = (
    (
        train_gap_analysis.loc[
            mask,
            "links_checked"
        ]
        -
        train_gap_analysis.loc[
            mask,
            "gap_count"
        ]
    )
    /
    train_gap_analysis.loc[
        mask,
        "links_checked"
    ]
    * 100
)


# ============================================================
# 14. GAP DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("GAP DISTRIBUTION PER TRAIN")
print("=" * 80)


print(
    train_gap_analysis["gap_count"]
    .describe()
)


# ============================================================
# 15. TRAINS WITH 10+ GAPS
# ============================================================

print("\n" + "=" * 80)
print("TRAINS WITH 10 OR MORE GAPS")
print("=" * 80)


many_gap_trains = (
    train_gap_analysis[
        train_gap_analysis["gap_count"] >= 10
    ]
    .sort_values(
        "gap_count",
        ascending=False
    )
)


print(
    "Number of trains:",
    len(many_gap_trains)
)


print(
    many_gap_trains.head(30)
    .to_string(index=False)
)


# ============================================================
# 16. INSPECT IMPORTANT EXAMPLES
# ============================================================

print("\n" + "=" * 80)
print("DETAILED GAP EXAMPLES")
print("=" * 80)


example_columns = [
    "train_number",
    "route_order",
    "previous_to_station",
    "previous_to_station_name",
    "from_station",
    "from_station_name",
    "to_station",
    "to_station_name",
    "previous_to_day",
    "from_day",
    "scheduled_run_minutes",
    "status",
    "gap_type"
]


print("\nFirst 50 gaps:\n")

print(
    gaps[
        example_columns
    ]
    .head(50)
    .to_string(index=False)
)


# ============================================================
# 17. INSPECT LOW-CONTINUITY TRAINS
# ============================================================

print("\n" + "=" * 80)
print("LOW-CONTINUITY TRAIN DETAILS")
print("=" * 80)


low_continuity_trains = (
    train_gap_analysis[
        (
            train_gap_analysis["links_checked"] >= 5
        )
        &
        (
            train_gap_analysis[
                "continuity_percentage"
            ] < 80
        )
    ]
    .sort_values(
        "continuity_percentage"
    )
)


print(
    "Low-continuity trains:",
    len(low_continuity_trains)
)


print(
    low_continuity_trains.head(20)
    .to_string(index=False)
)


# ============================================================
# 18. CHECK DAY TRANSITIONS AT GAPS
# ============================================================

print("\n" + "=" * 80)
print("DAY TRANSITIONS AT DISCONNECTED LINKS")
print("=" * 80)


gap_day_distribution = (
    gaps.groupby(
        [
            "previous_to_day",
            "from_day"
        ]
    )
    .size()
    .reset_index(
        name="gap_count"
    )
    .sort_values(
        "gap_count",
        ascending=False
    )
)


print(
    gap_day_distribution
    .to_string(index=False)
)


# ============================================================
# 19. FIND LARGE TIME GAPS BETWEEN RETAINED SEGMENTS
# ============================================================

print("\n" + "=" * 80)
print("GAPS INVOLVING LONG CURRENT SEGMENTS")
print("=" * 80)


large_current_segments = gaps[
    gaps["scheduled_run_minutes"] >= 60
].copy()


print(
    "Disconnected links with current segment >= 60 min:",
    len(large_current_segments)
)


if len(large_current_segments) > 0:

    print(
        large_current_segments[
            example_columns
        ]
        .sort_values(
            "scheduled_run_minutes",
            ascending=False
        )
        .head(30)
        .to_string(index=False)
    )


# ============================================================
# 20. SAVE DIAGNOSIS FILE
# ============================================================

gap_output = "gap_diagnosis_details.csv"

gaps.to_csv(
    gap_output,
    index=False
)

print(
    "\nSaved:",
    gap_output
)


# ============================================================
# 21. SAVE GAP PAIRS
# ============================================================

pair_output = "common_route_gap_pairs.csv"

gap_pairs.to_csv(
    pair_output,
    index=False
)

print(
    "Saved:",
    pair_output
)


# ============================================================
# 22. SAVE TRAIN GAP ANALYSIS
# ============================================================

train_output = (
    "train_gap_analysis.csv"
)

train_gap_analysis.to_csv(
    train_output,
    index=False
)

print(
    "Saved:",
    train_output
)


# ============================================================
# 23. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("STEP 3B FINAL SUMMARY")
print("=" * 80)

print(
    "Total disconnected links:",
    len(gaps)
)

print(
    "Affected trains:",
    len(train_gap_counts)
)

print(
    "Trains with 10+ gaps:",
    len(many_gap_trains)
)

print(
    "Low-continuity trains:",
    len(low_continuity_trains)
)

print(
    "Gap pairs identified:",
    len(gap_pairs)
)

print("\n✅ Step 3B completed successfully.")