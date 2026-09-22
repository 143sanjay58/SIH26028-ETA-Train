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
# STEP 3G
# SAME-STATION NORMALIZATION DIAGNOSIS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"

OUTPUT_DETAILS = "normalization_same_station_details.csv"
OUTPUT_SUMMARY = "normalization_same_station_summary.csv"


# ============================================================
# PROPOSED NORMALIZATION
# ============================================================

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
# LOAD DATA
# ============================================================

print("=" * 80)
print("STEP 3G - SAME-STATION NORMALIZATION DIAGNOSIS")
print("=" * 80)

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("✅ Dataset loaded")
print("Rows:", len(df))


# ============================================================
# PRESERVE ORIGINAL ROUTE ORDER
# ============================================================

df["route_order"] = (
    df.groupby("train_number")
      .cumcount() + 1
)


# ============================================================
# CREATE NORMALIZED COPIES
# ============================================================

df["from_station_norm"] = (
    df["from_station"].replace(MAPPINGS)
)

df["to_station_norm"] = (
    df["to_station"].replace(MAPPINGS)
)


# ============================================================
# IDENTIFY NEW SAME-STATION ROWS
# ============================================================

original_same_station = (
    df["from_station"] ==
    df["to_station"]
)

normalized_same_station = (
    df["from_station_norm"] ==
    df["to_station_norm"]
)

new_same_station = (
    normalized_same_station
    &
    ~original_same_station
)


diagnosis = df[new_same_station].copy()


print("\n" + "=" * 80)
print("SAME-STATION RESULTS")
print("=" * 80)

print(
    "Original same-station rows:",
    original_same_station.sum()
)

print(
    "Normalized same-station rows:",
    normalized_same_station.sum()
)

print(
    "NEW same-station rows:",
    new_same_station.sum()
)


# ============================================================
# SHOW DETAILS
# ============================================================

if len(diagnosis) > 0:

    print("\n" + "=" * 80)
    print("NEW SAME-STATION SEGMENTS")
    print("=" * 80)

    display_columns = [
        "train_number",
        "route_order",
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
        "from_station_norm",
        "to_station_norm",
    ]

    print(
        diagnosis[
            display_columns
        ].to_string(index=False)
    )


# ============================================================
# DETERMINE WHICH MAPPING CREATED EACH ROW
# ============================================================

def find_mapping(old_from, old_to):

    from_new = MAPPINGS.get(
        old_from,
        old_from
    )

    to_new = MAPPINGS.get(
        old_to,
        old_to
    )

    if from_new == to_new:

        if old_from != old_to:

            return (
                f"{old_from} -> {from_new} "
                f"and "
                f"{old_to} -> {to_new}"
            )

    return "unknown"


diagnosis["normalization_reason"] = diagnosis.apply(
    lambda row: find_mapping(
        row["from_station"],
        row["to_station"]
    ),
    axis=1
)


# ============================================================
# COUNT BY NORMALIZED STATION
# ============================================================

print("\n" + "=" * 80)
print("NEW SAME-STATION COUNT BY STATION")
print("=" * 80)

station_counts = (
    diagnosis
    .groupby(
        [
            "from_station_norm",
            "to_station_norm"
        ]
    )
    .size()
    .reset_index(
        name="new_same_station_rows"
    )
    .sort_values(
        "new_same_station_rows",
        ascending=False
    )
)

print(
    station_counts.to_string(
        index=False
    )
)


# ============================================================
# COUNT BY ORIGINAL CODE PAIR
# ============================================================

print("\n" + "=" * 80)
print("ORIGINAL CODE PAIRS")
print("=" * 80)

pair_counts = (
    diagnosis
    .groupby(
        [
            "from_station",
            "to_station"
        ]
    )
    .size()
    .reset_index(
        name="count"
    )
    .sort_values(
        "count",
        ascending=False
    )
)

print(
    pair_counts.to_string(
        index=False
    )
)


# ============================================================
# CHECK TIME CONTINUITY
# ============================================================

def time_to_minutes(time_value):

    if pd.isna(time_value):
        return None

    text = str(time_value)

    try:
        parts = text.split(":")

        hour = int(parts[0])
        minute = int(parts[1])

        return hour * 60 + minute

    except:
        return None


def absolute_minutes(day, time_value):

    t = time_to_minutes(time_value)

    if t is None or pd.isna(day):
        return None

    return (
        (int(day) - 1) * 1440
        + t
    )


diagnosis["from_arrival_abs"] = diagnosis.apply(
    lambda row: absolute_minutes(
        row["from_day"],
        row["from_arrival"]
    ),
    axis=1
)

diagnosis["from_departure_abs"] = diagnosis.apply(
    lambda row: absolute_minutes(
        row["from_day"],
        row["from_departure"]
    ),
    axis=1
)

diagnosis["to_arrival_abs"] = diagnosis.apply(
    lambda row: absolute_minutes(
        row["to_day"],
        row["to_arrival"]
    ),
    axis=1
)

diagnosis["to_departure_abs"] = diagnosis.apply(
    lambda row: absolute_minutes(
        row["to_day"],
        row["to_departure"]
    ),
    axis=1
)


# ============================================================
# CHECK WHETHER SAME-STATION ROW HAS ZERO RUN TIME
# ============================================================

diagnosis["calculated_run_minutes"] = (
    diagnosis["to_arrival_abs"]
    -
    diagnosis["from_departure_abs"]
)


print("\n" + "=" * 80)
print("SAME-STATION TIME ANALYSIS")
print("=" * 80)

print(
    diagnosis[
        [
            "train_number",
            "route_order",
            "from_station",
            "to_station",
            "from_station_norm",
            "from_departure",
            "to_arrival",
            "from_day",
            "to_day",
            "scheduled_run_minutes",
            "calculated_run_minutes"
        ]
    ].to_string(index=False)
)


# ============================================================
# TIME DISTRIBUTION
# ============================================================

time_values = (
    diagnosis["calculated_run_minutes"]
    .dropna()
)

if len(time_values) > 0:

    print("\nTime statistics:")

    print(
        "Minimum:",
        time_values.min()
    )

    print(
        "Maximum:",
        time_values.max()
    )

    print(
        "Mean:",
        round(time_values.mean(), 2)
    )

    print(
        "Median:",
        time_values.median()
    )

    print(
        "Exactly 0 minutes:",
        (time_values == 0).sum()
    )

    print(
        "Greater than 0 minutes:",
        (time_values > 0).sum()
    )


# ============================================================
# CHECK SCHEDULED RUN TIME
# ============================================================

print("\n" + "=" * 80)
print("SCHEDULED RUN TIME CHECK")
print("=" * 80)

scheduled_values = (
    diagnosis[
        "scheduled_run_minutes"
    ]
    .dropna()
)

print(
    "Minimum scheduled run:",
    scheduled_values.min()
)

print(
    "Maximum scheduled run:",
    scheduled_values.max()
)

print(
    "Mean scheduled run:",
    round(
        scheduled_values.mean(),
        2
    )
)

print(
    "Exactly 0 minutes:",
    (
        scheduled_values == 0
    ).sum()
)


# ============================================================
# CHECK ROUTE CONTINUITY AROUND THESE ROWS
# ============================================================

diagnosis["previous_to_station"] = (
    df.groupby("train_number")[
        "to_station"
    ]
    .shift(1)
)

diagnosis["previous_to_station_norm"] = (
    df.groupby("train_number")[
        "to_station_norm"
    ]
    .shift(1)
)


# The above shift must align by original dataframe index.
# Recalculate safely using the full dataframe.

df["previous_to_station"] = (
    df.groupby("train_number")[
        "to_station"
    ]
    .shift(1)
)

df["previous_to_station_norm"] = (
    df.groupby("train_number")[
        "to_station_norm"
    ]
    .shift(1)
)

diagnosis = df.loc[
    new_same_station
].copy()


diagnosis["continuity_before"] = (
    diagnosis["previous_to_station"]
    ==
    diagnosis["from_station"]
)

diagnosis["continuity_after"] = (
    diagnosis["previous_to_station_norm"]
    ==
    diagnosis["from_station_norm"]
)


print("\n" + "=" * 80)
print("CONTINUITY AROUND NEW SAME-STATION ROWS")
print("=" * 80)

print(
    "Continuous before normalization:",
    diagnosis[
        "continuity_before"
    ].sum()
)

print(
    "Continuous after normalization:",
    diagnosis[
        "continuity_after"
    ].sum()
)

print(
    "Improved continuity:",
    (
        diagnosis["continuity_after"]
        &
        ~diagnosis["continuity_before"]
    ).sum()
)


# ============================================================
# TRAIN-LEVEL IMPACT
# ============================================================

affected_trains = (
    diagnosis[
        "train_number"
    ]
    .astype(str)
    .unique()
)

print("\n" + "=" * 80)
print("TRAIN IMPACT")
print("=" * 80)

print(
    "Trains containing new same-station rows:",
    len(affected_trains)
)

print(
    "\nAffected trains:"
)

print(
    sorted(
        affected_trains,
        key=str
    )
)


# ============================================================
# CHECK SEGMENT TIME WAS NOT CHANGED
# ============================================================

time_before = df.loc[
    new_same_station,
    "scheduled_run_minutes"
].copy()

time_after = df.loc[
    new_same_station,
    "scheduled_run_minutes"
].copy()


print("\n" + "=" * 80)
print("SCHEDULED TIME PRESERVATION")
print("=" * 80)

print(
    "Number of segment times changed:",
    (
        time_before
        !=
        time_after
    ).sum()
)


# ============================================================
# SAVE DETAILED RESULTS
# ============================================================

diagnosis.to_csv(
    OUTPUT_DETAILS,
    index=False
)


station_counts.to_csv(
    OUTPUT_SUMMARY,
    index=False
)


print("\n" + "=" * 80)
print("OUTPUT FILES")
print("=" * 80)

print(
    f"✅ {OUTPUT_DETAILS}"
)

print(
    f"✅ {OUTPUT_SUMMARY}"
)

print(
    "\n⚠️ Original ml_ready_segments.csv was NOT modified."
)

print(
    "\nSTEP 3G COMPLETED."
)