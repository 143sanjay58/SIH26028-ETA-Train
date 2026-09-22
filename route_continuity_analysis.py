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
# STEP 3A - ROUTE CONTINUITY ANALYSIS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"


print("=" * 80)
print("STEP 3A - ROUTE CONTINUITY ANALYSIS")
print("=" * 80)


# ============================================================
# 1. CHECK FILE
# ============================================================

if not os.path.exists(DATASET1_PATH):
    print("\n❌ Dataset 1 file not found!")
    print("Expected:")
    print(os.path.abspath(DATASET1_PATH))
    raise SystemExit


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("✅ Dataset 1 loaded")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
for col in df.columns:
    print(" -", col)


# ============================================================
# 3. BASIC VALIDATION
# ============================================================

required_columns = [
    "train_number",
    "from_station",
    "to_station",
    "from_day",
    "to_day",
    "scheduled_run_minutes",
    "status"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    print("\n❌ Required columns missing:")
    for col in missing_columns:
        print(" -", col)

    raise SystemExit


# ============================================================
# 4. PRESERVE ORIGINAL ROUTE ORDER
# ============================================================

# The cleaned timetable was generated in route order.
# Therefore we preserve the CSV row order within each train.

df["route_order"] = df.groupby(
    "train_number"
).cumcount() + 1


# ============================================================
# 5. BASIC STATUS DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("STATUS DISTRIBUTION")
print("=" * 80)

status_counts = df["status"].value_counts()

print(status_counts)


# ============================================================
# 6. CHECK CONTINUITY BETWEEN SEGMENTS
# ============================================================

print("\n" + "=" * 80)
print("CHECKING ROUTE CONTINUITY")
print("=" * 80)


# Previous segment's destination
df["previous_to_station"] = (
    df.groupby("train_number")["to_station"]
    .shift(1)
)


# Current segment's origin
df["current_from_station"] = df["from_station"]


# First segment of every train has no previous segment
df["is_first_segment"] = (
    df["previous_to_station"].isna()
)


# A segment is continuous when:
#
# previous segment:
#     A -> B
#
# current segment:
#     B -> C
#
# Therefore:
#     previous_to_station == current_from_station

df["is_continuous"] = (
    df["is_first_segment"]
    |
    (
        df["previous_to_station"]
        ==
        df["current_from_station"]
    )
)


# ============================================================
# 7. COUNT CONTINUOUS / DISCONNECTED LINKS
# ============================================================

checked_links = df[
    ~df["is_first_segment"]
]

continuous_links = checked_links[
    checked_links["is_continuous"]
]

disconnected_links = checked_links[
    ~checked_links["is_continuous"]
]


print("\nTotal segments:", len(df))

print(
    "Links checked:",
    len(checked_links)
)

print(
    "Continuous links:",
    len(continuous_links)
)

print(
    "Disconnected links:",
    len(disconnected_links)
)


if len(checked_links) > 0:

    continuity_percentage = (
        len(continuous_links)
        / len(checked_links)
        * 100
    )

    print(
        f"Continuity percentage: "
        f"{continuity_percentage:.2f}%"
    )


# ============================================================
# 8. SHOW DISCONNECTED ROUTES
# ============================================================

print("\n" + "=" * 80)
print("DISCONNECTED ROUTE LINKS")
print("=" * 80)


if len(disconnected_links) == 0:

    print("✅ No disconnected links found.")

else:

    print(
        f"⚠️ Found {len(disconnected_links)} "
        "disconnected links."
    )

    print("\nFirst 30 examples:\n")

    display_columns = [
        "train_number",
        "route_order",
        "previous_to_station",
        "current_from_station",
        "from_station",
        "to_station",
        "from_day",
        "to_day",
        "scheduled_run_minutes",
        "status"
    ]

    print(
        disconnected_links[
            display_columns
        ].head(30).to_string(index=False)
    )


# ============================================================
# 9. TRAIN-LEVEL CONTINUITY SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("TRAIN-LEVEL ROUTE SUMMARY")
print("=" * 80)


train_summary = (
    df.groupby("train_number")
    .agg(
        total_segments=(
            "train_number",
            "size"
        ),

        continuous_links=(
            "is_continuous",
            lambda x: (
                x.iloc[1:].sum()
                if len(x) > 1
                else 0
            )
        ),

        total_run_minutes=(
            "scheduled_run_minutes",
            "sum"
        ),

        max_segment_minutes=(
            "scheduled_run_minutes",
            "max"
        ),

        min_segment_minutes=(
            "scheduled_run_minutes",
            "min"
        )
    )
    .reset_index()
)


# Number of links for each train = segments - 1
train_summary["links_checked"] = (
    train_summary["total_segments"] - 1
)


train_summary["disconnected_links"] = (
    train_summary["links_checked"]
    -
    train_summary["continuous_links"]
)


# Avoid division by zero for trains with only one segment
train_summary["continuity_percentage"] = 100.0

mask = train_summary["links_checked"] > 0

train_summary.loc[
    mask,
    "continuity_percentage"
] = (
    train_summary.loc[
        mask,
        "continuous_links"
    ]
    /
    train_summary.loc[
        mask,
        "links_checked"
    ]
    * 100
)


# ============================================================
# 10. SUMMARY STATISTICS
# ============================================================

print("\nTotal trains:", len(train_summary))

print(
    "Average segments per train:",
    round(
        train_summary["total_segments"].mean(),
        2
    )
)

print(
    "Average scheduled segment time:",
    round(
        df["scheduled_run_minutes"].mean(),
        2
    ),
    "minutes"
)

print(
    "Maximum scheduled segment time:",
    df["scheduled_run_minutes"].max(),
    "minutes"
)


# ============================================================
# 11. TRAINS WITH MOST DISCONNECTED LINKS
# ============================================================

print("\n" + "=" * 80)
print("TRAINS WITH MOST DISCONNECTED LINKS")
print("=" * 80)


most_disconnected = (
    train_summary
    .sort_values(
        "disconnected_links",
        ascending=False
    )
    .head(20)
)


print(
    most_disconnected[
        [
            "train_number",
            "total_segments",
            "links_checked",
            "continuous_links",
            "disconnected_links",
            "continuity_percentage"
        ]
    ].to_string(index=False)
)


# ============================================================
# 12. TRAINS WITH LOW CONTINUITY
# ============================================================

print("\n" + "=" * 80)
print("TRAINS WITH LOW ROUTE CONTINUITY")
print("=" * 80)


low_continuity = train_summary[
    (train_summary["links_checked"] >= 5)
    &
    (train_summary["continuity_percentage"] < 80)
].sort_values(
    "continuity_percentage"
)


print(
    "Number of trains with continuity below 80%:",
    len(low_continuity)
)


if len(low_continuity) > 0:

    print("\nFirst 20 examples:\n")

    print(
        low_continuity[
            [
                "train_number",
                "total_segments",
                "links_checked",
                "continuous_links",
                "disconnected_links",
                "continuity_percentage"
            ]
        ].head(20).to_string(index=False)
    )


# ============================================================
# 13. SEGMENT LENGTH ANALYSIS
# ============================================================

print("\n" + "=" * 80)
print("LONG SCHEDULED SEGMENTS")
print("=" * 80)


long_segments = df[
    df["scheduled_run_minutes"] >= 180
].copy()


print(
    "Segments >= 180 minutes:",
    len(long_segments)
)


if len(long_segments) > 0:

    print("\nTop 30 longest segments:\n")

    print(
        long_segments[
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_day",
                "to_day",
                "scheduled_run_minutes",
                "status"
            ]
        ]
        .sort_values(
            "scheduled_run_minutes",
            ascending=False
        )
        .head(30)
        .to_string(index=False)
    )


# ============================================================
# 14. DAY TRANSITION ANALYSIS
# ============================================================

print("\n" + "=" * 80)
print("DAY TRANSITION ANALYSIS")
print("=" * 80)


day_transition_counts = (
    df.groupby(
        ["from_day", "to_day"]
    )
    .size()
    .reset_index(
        name="segment_count"
    )
    .sort_values(
        "segment_count",
        ascending=False
    )
)


print(
    day_transition_counts.to_string(
        index=False
    )
)


# ============================================================
# 15. CHECK UNUSUAL DAY TRANSITIONS
# ============================================================

unusual_day_transitions = df[
    (
        df["to_day"]
        <
        df["from_day"]
    )
]


print(
    "\nSegments where to_day < from_day:",
    len(unusual_day_transitions)
)


if len(unusual_day_transitions) > 0:

    print("\n⚠️ Examples:\n")

    print(
        unusual_day_transitions[
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_day",
                "to_day",
                "scheduled_run_minutes"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

else:

    print(
        "✅ No backward day transitions found."
    )


# ============================================================
# 16. SAVE DISCONNECTED LINKS
# ============================================================

disconnected_output = (
    "disconnected_route_links.csv"
)

disconnected_links.to_csv(
    disconnected_output,
    index=False
)

print(
    "\nSaved:",
    disconnected_output
)


# ============================================================
# 17. SAVE TRAIN SUMMARY
# ============================================================

summary_output = (
    "train_route_continuity_summary.csv"
)

train_summary.to_csv(
    summary_output,
    index=False
)

print(
    "Saved:",
    summary_output
)


# ============================================================
# 18. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("STEP 3A FINAL SUMMARY")
print("=" * 80)

print(
    "Total trains:",
    len(train_summary)
)

print(
    "Total route segments:",
    len(df)
)

print(
    "Continuous links:",
    len(continuous_links)
)

print(
    "Disconnected links:",
    len(disconnected_links)
)

if len(checked_links) > 0:

    print(
        "Overall continuity:",
        f"{continuity_percentage:.2f}%"
    )

print(
    "Long segments >= 180 min:",
    len(long_segments)
)

print(
    "Backward day transitions:",
    len(unusual_day_transitions)
)

print("\n✅ Step 3A analysis completed.")