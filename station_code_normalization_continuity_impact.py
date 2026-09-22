import pandas as pd
import numpy as np

# ============================================================
# STEP 3H
# STATION CODE NORMALIZATION - CONTINUITY IMPACT ANALYSIS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"


# ------------------------------------------------------------
# PROPOSED STATION CODE MAPPINGS
# ------------------------------------------------------------
# We are NOT modifying the original dataset.
# These mappings are applied only to an in-memory copy.

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
print("STEP 3H - STATION CODE NORMALIZATION CONTINUITY IMPACT")
print("=" * 80)

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("Dataset loaded")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 2. PRESERVE ORIGINAL ROUTE ORDER
# ============================================================

print("\nPreparing route order...")

df["route_order"] = (
    df.groupby("train_number")
      .cumcount() + 1
)


# ============================================================
# 3. CREATE PREVIOUS/NEXT STATION INFORMATION
# ============================================================

print("Creating route continuity information...")

# Previous segment's destination station
df["previous_to"] = (
    df.groupby("train_number")["to_station"]
      .shift(1)
)

# Next segment's source station
df["next_from"] = (
    df.groupby("train_number")["from_station"]
      .shift(-1)
)


# ============================================================
# 4. ORIGINAL CONTINUITY
# ============================================================

print("Calculating ORIGINAL route continuity...")

df["continuous_before"] = (
    df["previous_to"] == df["from_station"]
).astype("boolean")

df["continuous_after"] = (
    df["to_station"] == df["next_from"]
).astype("boolean")


# First segment has no previous segment
first_segment = df["route_order"] == 1

df.loc[
    first_segment,
    "continuous_before"
] = pd.NA


# Last segment has no next segment
last_segment = (
    df["route_order"]
    ==
    df.groupby("train_number")["route_order"].transform("max")
)

df.loc[
    last_segment,
    "continuous_after"
] = pd.NA


# ============================================================
# 5. CREATE NORMALIZED COPY
# ============================================================

print("\nApplying proposed normalization in memory...")

normalized_df = df.copy()


# Normalize FROM station
normalized_df["from_station_normalized"] = (
    normalized_df["from_station"]
    .map(MAPPINGS)
    .fillna(normalized_df["from_station"])
)


# Normalize TO station
normalized_df["to_station_normalized"] = (
    normalized_df["to_station"]
    .map(MAPPINGS)
    .fillna(normalized_df["to_station"])
)


# Normalize previous TO station
normalized_df["previous_to_normalized"] = (
    normalized_df["previous_to"]
    .map(MAPPINGS)
    .fillna(normalized_df["previous_to"])
)


# Normalize next FROM station
normalized_df["next_from_normalized"] = (
    normalized_df["next_from"]
    .map(MAPPINGS)
    .fillna(normalized_df["next_from"])
)


# ============================================================
# 6. NORMALIZED CONTINUITY
# ============================================================

print("Calculating NORMALIZED route continuity...")

normalized_df["continuous_before_normalized"] = (
    normalized_df["previous_to_normalized"]
    ==
    normalized_df["from_station_normalized"]
).astype("boolean")


normalized_df["continuous_after_normalized"] = (
    normalized_df["to_station_normalized"]
    ==
    normalized_df["next_from_normalized"]
).astype("boolean")


# First segment
normalized_df.loc[
    first_segment,
    "continuous_before_normalized"
] = pd.NA


# Last segment
normalized_df.loc[
    last_segment,
    "continuous_after_normalized"
] = pd.NA


# ============================================================
# 7. OVERALL CONTINUITY STATISTICS
# ============================================================

print("\n" + "=" * 80)
print("OVERALL CONTINUITY")
print("=" * 80)


# Only compare links that actually have a previous segment
valid_before = normalized_df["continuous_before"].notna()


original_continuous = (
    normalized_df.loc[
        valid_before,
        "continuous_before"
    ].sum()
)


normalized_continuous = (
    normalized_df.loc[
        valid_before,
        "continuous_before_normalized"
    ].sum()
)


total_links = valid_before.sum()


original_gaps = total_links - original_continuous

normalized_gaps = total_links - normalized_continuous


original_percentage = (
    original_continuous / total_links * 100
)


normalized_percentage = (
    normalized_continuous / total_links * 100
)


improvement = (
    normalized_percentage -
    original_percentage
)


print("\nTotal route links:", total_links)

print("\nORIGINAL:")
print("Continuous links:", int(original_continuous))
print("Disconnected links:", int(original_gaps))
print(
    "Continuity percentage:",
    round(original_percentage, 2),
    "%"
)


print("\nNORMALIZED:")
print("Continuous links:", int(normalized_continuous))
print("Disconnected links:", int(normalized_gaps))
print(
    "Continuity percentage:",
    round(normalized_percentage, 2),
    "%"
)


print("\nIMPACT:")
print(
    "Continuity improvement:",
    round(improvement, 2),
    "percentage points"
)

print(
    "Gaps eliminated:",
    int(original_gaps - normalized_gaps)
)


# ============================================================
# 8. LINK-LEVEL IMPACT CLASSIFICATION
# ============================================================

print("\n" + "=" * 80)
print("LINK-LEVEL NORMALIZATION IMPACT")
print("=" * 80)


comparison = normalized_df.loc[
    valid_before,
    [
        "train_number",
        "route_order",
        "previous_to",
        "from_station",
        "previous_to_normalized",
        "from_station_normalized",
        "continuous_before",
        "continuous_before_normalized",
    ]
].copy()


# Classify each link
def classify_link(row):

    original = row["continuous_before"]
    normalized = row["continuous_before_normalized"]

    if original is True and normalized is True:
        return "continuous_before_and_after"

    elif original is False and normalized is True:
        return "gap_eliminated"

    elif original is True and normalized is False:
        return "new_gap_created"

    elif original is False and normalized is False:
        return "gap_remains"

    else:
        return "unknown"


comparison["impact"] = comparison.apply(
    classify_link,
    axis=1
)


impact_counts = (
    comparison["impact"]
    .value_counts()
)


print("\nLink impact distribution:")

for impact_type, count in impact_counts.items():

    print(
        f"{impact_type:<35} {count}"
    )


# ============================================================
# 9. SHOW GAP ELIMINATED DETAILS
# ============================================================

gap_eliminated = comparison[
    comparison["impact"] == "gap_eliminated"
].copy()


print("\n" + "=" * 80)
print("GAPS ELIMINATED BY NORMALIZATION")
print("=" * 80)

print(
    "Total gaps eliminated:",
    len(gap_eliminated)
)


if len(gap_eliminated) > 0:

    print("\nSample eliminated gaps:")

    print(
        gap_eliminated[
            [
                "train_number",
                "route_order",
                "previous_to",
                "from_station",
                "previous_to_normalized",
                "from_station_normalized",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

else:

    print("\nNo gaps were eliminated.")


# ============================================================
# 10. SHOW NEW GAPS CREATED
# ============================================================

new_gaps = comparison[
    comparison["impact"] == "new_gap_created"
].copy()


print("\n" + "=" * 80)
print("NEW GAPS CREATED BY NORMALIZATION")
print("=" * 80)

print(
    "Total new gaps:",
    len(new_gaps)
)


if len(new_gaps) > 0:

    print("\nWARNING: New gaps were created.")

    print("\nSample new gaps:")

    print(
        new_gaps[
            [
                "train_number",
                "route_order",
                "previous_to",
                "from_station",
                "previous_to_normalized",
                "from_station_normalized",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

else:

    print("\nNo new gaps were created.")


# ============================================================
# 11. TRAIN-LEVEL CONTINUITY IMPACT
# ============================================================

print("\n" + "=" * 80)
print("TRAIN-LEVEL CONTINUITY IMPACT")
print("=" * 80)


train_impact = (
    comparison
    .groupby("train_number")
    .agg(
        total_links=(
            "continuous_before",
            "count"
        ),

        original_continuous=(
            "continuous_before",
            "sum"
        ),

        normalized_continuous=(
            "continuous_before_normalized",
            "sum"
        )
    )
    .reset_index()
)


train_impact["original_gaps"] = (
    train_impact["total_links"]
    -
    train_impact["original_continuous"]
)


train_impact["normalized_gaps"] = (
    train_impact["total_links"]
    -
    train_impact["normalized_continuous"]
)


train_impact["original_continuity_pct"] = (
    train_impact["original_continuous"]
    /
    train_impact["total_links"]
    *
    100
)


train_impact["normalized_continuity_pct"] = (
    train_impact["normalized_continuous"]
    /
    train_impact["total_links"]
    *
    100
)


train_impact["improvement_pct_points"] = (
    train_impact["normalized_continuity_pct"]
    -
    train_impact["original_continuity_pct"]
)


# ============================================================
# 12. TRAIN SUMMARY
# ============================================================

improved_trains = train_impact[
    train_impact["improvement_pct_points"] > 0
]


unchanged_trains = train_impact[
    train_impact["improvement_pct_points"] == 0
]


worsened_trains = train_impact[
    train_impact["improvement_pct_points"] < 0
]


print("\nTotal trains analyzed:", len(train_impact))

print(
    "Trains improved:",
    len(improved_trains)
)

print(
    "Trains unchanged:",
    len(unchanged_trains)
)

print(
    "Trains worsened:",
    len(worsened_trains)
)


# ============================================================
# 13. TOP IMPROVED TRAINS
# ============================================================

print("\n" + "=" * 80)
print("TOP 20 IMPROVED TRAINS")
print("=" * 80)


if len(improved_trains) > 0:

    print(
        improved_trains
        .sort_values(
            "improvement_pct_points",
            ascending=False
        )
        .head(20)
        .to_string(index=False)
    )

else:

    print("\nNo trains improved.")


# ============================================================
# 14. WORST / NEWLY AFFECTED TRAINS
# ============================================================

print("\n" + "=" * 80)
print("TRAINS WITH NEGATIVE IMPACT")
print("=" * 80)


if len(worsened_trains) > 0:

    print(
        worsened_trains
        .sort_values(
            "improvement_pct_points"
        )
        .head(20)
        .to_string(index=False)
    )

else:

    print("\nNo trains were negatively affected.")


# ============================================================
# 15. PAIR-WISE NORMALIZATION IMPACT
# ============================================================

print("\n" + "=" * 80)
print("PAIR-WISE NORMALIZATION IMPACT")
print("=" * 80)


pair_results = []


for old_code, new_code in MAPPINGS.items():

    # Links where either side contains the old code
    affected = comparison[
        (
            comparison["previous_to"] == old_code
        )
        |
        (
            comparison["from_station"] == old_code
        )
    ]


    eliminated = affected[
        affected["impact"] == "gap_eliminated"
    ]


    created = affected[
        affected["impact"] == "new_gap_created"
    ]


    remaining = affected[
        affected["impact"] == "gap_remains"
    ]


    pair_results.append(
        {
            "old_code": old_code,
            "new_code": new_code,
            "affected_links": len(affected),
            "gaps_eliminated": len(eliminated),
            "new_gaps_created": len(created),
            "gaps_remaining": len(remaining),
        }
    )


pair_df = pd.DataFrame(pair_results)


print(
    pair_df.to_string(index=False)
)


# ============================================================
# 16. SAVE TRAIN-LEVEL RESULTS
# ============================================================

train_output = (
    "normalization_continuity_train_impact.csv"
)

train_impact.to_csv(
    train_output,
    index=False
)


# ============================================================
# 17. SAVE LINK-LEVEL RESULTS
# ============================================================

link_output = (
    "normalization_continuity_link_impact.csv"
)

comparison.to_csv(
    link_output,
    index=False
)


# ============================================================
# 18. SAVE PAIR-LEVEL RESULTS
# ============================================================

pair_output = (
    "normalization_continuity_pair_impact.csv"
)

pair_df.to_csv(
    pair_output,
    index=False
)


# ============================================================
# 19. SAVE OVERALL SUMMARY
# ============================================================

summary = pd.DataFrame(
    [
        {
            "total_rows": len(df),

            "total_route_links": int(total_links),

            "original_continuous_links":
                int(original_continuous),

            "normalized_continuous_links":
                int(normalized_continuous),

            "original_gaps":
                int(original_gaps),

            "normalized_gaps":
                int(normalized_gaps),

            "gaps_eliminated":
                int(original_gaps - normalized_gaps),

            "continuity_before_pct":
                round(
                    original_percentage,
                    4
                ),

            "continuity_after_pct":
                round(
                    normalized_percentage,
                    4
                ),

            "continuity_improvement_pct_points":
                round(
                    improvement,
                    4
                ),

            "trains_improved":
                len(improved_trains),

            "trains_unchanged":
                len(unchanged_trains),

            "trains_worsened":
                len(worsened_trains),
        }
    ]
)


summary_output = (
    "normalization_continuity_summary.csv"
)


summary.to_csv(
    summary_output,
    index=False
)


# ============================================================
# 20. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("FINAL STEP 3H SUMMARY")
print("=" * 80)

print(
    "\nOriginal continuity:",
    round(original_percentage, 2),
    "%"
)

print(
    "Normalized continuity:",
    round(normalized_percentage, 2),
    "%"
)

print(
    "Improvement:",
    round(improvement, 2),
    "percentage points"
)

print(
    "Gaps eliminated:",
    int(original_gaps - normalized_gaps)
)

print(
    "New gaps created:",
    len(new_gaps)
)

print(
    "Trains improved:",
    len(improved_trains)
)

print(
    "Trains unchanged:",
    len(unchanged_trains)
)

print(
    "Trains worsened:",
    len(worsened_trains)
)


print("\nFiles saved:")

print(
    "1.",
    train_output
)

print(
    "2.",
    link_output
)

print(
    "3.",
    pair_output
)

print(
    "4.",
    summary_output
)


print("\nOriginal ml_ready_segments.csv was NOT modified.")

print("\n" + "=" * 80)
print("STEP 3H COMPLETED")
print("=" * 80)