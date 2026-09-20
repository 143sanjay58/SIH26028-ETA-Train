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
import re
from pathlib import Path


# ============================================================
# STEP 3C - STATION CODE NORMALIZATION ANALYSIS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"
GAP_FILE_PATH = "gap_diagnosis_details.csv"

OUTPUT_EXACT = "station_code_exact_name_candidates.csv"
OUTPUT_AMBIGUOUS = "station_code_ambiguous_groups.csv"
OUTPUT_GAPS = "station_code_gap_candidates.csv"


# ============================================================
# 1. LOAD DATASET 1
# ============================================================

print("=" * 80)
print("STEP 3C - STATION CODE NORMALIZATION ANALYSIS")
print("=" * 80)

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("✅ Dataset 1 loaded")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 2. CREATE STATION MASTER TABLE
# ============================================================

print("\n" + "=" * 80)
print("BUILDING STATION MASTER TABLE")
print("=" * 80)

from_stations = df[
    ["from_station", "from_station_name"]
].rename(
    columns={
        "from_station": "station_code",
        "from_station_name": "station_name"
    }
)

to_stations = df[
    ["to_station", "to_station_name"]
].rename(
    columns={
        "to_station": "station_code",
        "to_station_name": "station_name"
    }
)

stations = pd.concat(
    [from_stations, to_stations],
    ignore_index=True
)

# Remove exact duplicate rows
stations = stations.drop_duplicates()

# Remove missing values
stations = stations.dropna(
    subset=["station_code", "station_name"]
)

print(f"Unique code-name combinations: {len(stations)}")
print(f"Unique station codes: {stations['station_code'].nunique()}")
print(f"Unique station names: {stations['station_name'].nunique()}")


# ============================================================
# 3. NORMALIZE STATION NAMES
# ============================================================

def normalize_station_name(name):
    """
    Conservative normalization.

    This is ONLY used for finding candidates.
    It does NOT mean two stations are actually identical.
    """

    name = str(name).upper().strip()

    # Replace punctuation with spaces
    name = re.sub(r"[^A-Z0-9]+", " ", name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)

    return name.strip()


stations["normalized_name"] = stations[
    "station_name"
].apply(normalize_station_name)


# ============================================================
# 4. FIND EXACT SAME-NAME / DIFFERENT-CODE GROUPS
# ============================================================

print("\n" + "=" * 80)
print("EXACT NAME / DIFFERENT CODE ANALYSIS")
print("=" * 80)

name_code_counts = (
    stations
    .groupby("normalized_name")["station_code"]
    .nunique()
)

candidate_names = name_code_counts[
    name_code_counts > 1
].index

exact_candidates = stations[
    stations["normalized_name"].isin(candidate_names)
].copy()

exact_candidates = exact_candidates.sort_values(
    ["normalized_name", "station_code"]
)

print(
    f"Station names represented by multiple codes: "
    f"{len(candidate_names)}"
)

print(
    f"Candidate code-name records: "
    f"{len(exact_candidates)}"
)


# ============================================================
# 5. CREATE PAIRWISE CODE CANDIDATES
# ============================================================

print("\n" + "=" * 80)
print("CREATING CODE PAIR CANDIDATES")
print("=" * 80)

pair_records = []

for normalized_name, group in exact_candidates.groupby(
    "normalized_name"
):

    codes = sorted(
        group["station_code"].unique()
    )

    names = sorted(
        group["station_name"].unique()
    )

    # Create every possible pair
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):

            code_a = codes[i]
            code_b = codes[j]

            pair_records.append({
                "normalized_name": normalized_name,
                "code_a": code_a,
                "code_b": code_b,
                "station_names": " | ".join(names),
                "number_of_codes": len(codes)
            })


pair_df = pd.DataFrame(pair_records)

if len(pair_df) > 0:

    pair_df = pair_df.sort_values(
        ["normalized_name", "code_a", "code_b"]
    )

    print(
        f"Candidate code pairs found: "
        f"{len(pair_df)}"
    )

else:

    print("No same-name/different-code pairs found.")


# ============================================================
# 6. CHECK HOW OFTEN EACH CODE PAIR OCCURS AS A ROUTE GAP
# ============================================================

print("\n" + "=" * 80)
print("CHECKING CODE PAIRS AGAINST ROUTE GAPS")
print("=" * 80)

# Previous station -> current station
df["previous_to_station"] = (
    df.groupby("train_number")["to_station"]
    .shift(1)
)

df["previous_to_station_name"] = (
    df.groupby("train_number")["to_station_name"]
    .shift(1)
)

# Identify route gaps
df["is_gap"] = (
    df["previous_to_station"].notna()
    &
    (
        df["previous_to_station"]
        !=
        df["from_station"]
    )
)

gap_df = df[
    df["is_gap"]
].copy()

print(f"Total route gaps checked: {len(gap_df)}")


# ============================================================
# 7. BUILD GAP CODE-PAIR TABLE
# ============================================================

gap_pairs = []

for _, row in gap_df.iterrows():

    previous_code = row["previous_to_station"]
    current_code = row["from_station"]

    previous_name = row["previous_to_station_name"]
    current_name = row["from_station_name"]

    previous_norm = normalize_station_name(
        previous_name
    )

    current_norm = normalize_station_name(
        current_name
    )

    # Only interesting when names are exactly equal
    if (
        previous_norm == current_norm
        and
        previous_code != current_code
    ):

        gap_pairs.append({
            "previous_code": previous_code,
            "current_code": current_code,
            "station_name": previous_name,
            "train_number": row["train_number"],
            "route_order": row["route_order"]
            if "route_order" in row
            else None
        })


gap_pair_df = pd.DataFrame(gap_pairs)


# ============================================================
# 8. SUMMARIZE GAP PAIRS
# ============================================================

if len(gap_pair_df) > 0:

    gap_summary = (
        gap_pair_df
        .groupby(
            [
                "previous_code",
                "current_code",
                "station_name"
            ]
        )
        .agg(
            gap_occurrences=(
                "train_number",
                "count"
            ),
            affected_trains=(
                "train_number",
                "nunique"
            )
        )
        .reset_index()
        .sort_values(
            "gap_occurrences",
            ascending=False
        )
    )

else:

    gap_summary = pd.DataFrame(
        columns=[
            "previous_code",
            "current_code",
            "station_name",
            "gap_occurrences",
            "affected_trains"
        ]
    )


# ============================================================
# 9. DISPLAY HIGH-CONFIDENCE-LOOKING CANDIDATES
# ============================================================

print("\n" + "=" * 80)
print("POSSIBLE CODE VARIATIONS IN ROUTE GAPS")
print("=" * 80)

if len(gap_summary) > 0:

    print(
        gap_summary.head(30).to_string(
            index=False
        )
    )

else:

    print("No exact-name code variations found in gaps.")


# ============================================================
# 10. MERGE GLOBAL NAME INFORMATION WITH GAP INFORMATION
# ============================================================

if len(pair_df) > 0:

    pair_df["code_pair"] = (
        pair_df["code_a"]
        + " <-> "
        + pair_df["code_b"]
    )

    # Convert gap pair into unordered pair
    if len(gap_summary) > 0:

        gap_summary["code_a"] = gap_summary[
            ["previous_code", "current_code"]
        ].min(axis=1)

        gap_summary["code_b"] = gap_summary[
            ["previous_code", "current_code"]
        ].max(axis=1)

        gap_summary["code_pair"] = (
            gap_summary["code_a"]
            + " <-> "
            + gap_summary["code_b"]
        )

        gap_stats = (
            gap_summary
            .groupby("code_pair")
            .agg(
                total_gap_occurrences=(
                    "gap_occurrences",
                    "sum"
                ),
                affected_trains=(
                    "affected_trains",
                    "sum"
                )
            )
            .reset_index()
        )

        pair_df = pair_df.merge(
            gap_stats,
            on="code_pair",
            how="left"
        )

    else:

        pair_df["total_gap_occurrences"] = 0
        pair_df["affected_trains"] = 0

    pair_df[
        "total_gap_occurrences"
    ] = pair_df[
        "total_gap_occurrences"
    ].fillna(0)

    pair_df[
        "affected_trains"
    ] = pair_df[
        "affected_trains"
    ].fillna(0)


# ============================================================
# 11. CANDIDATE CLASSIFICATION
# ============================================================

print("\n" + "=" * 80)
print("CANDIDATE CLASSIFICATION")
print("=" * 80)

if len(pair_df) > 0:

    def classify(row):

        gap_count = row[
            "total_gap_occurrences"
        ]

        if gap_count >= 20:
            return "HIGH_PRIORITY_REVIEW"

        elif gap_count >= 5:
            return "MEDIUM_PRIORITY_REVIEW"

        elif gap_count > 0:
            return "LOW_PRIORITY_REVIEW"

        else:
            return "NAME_MATCH_ONLY"

    pair_df["review_priority"] = pair_df.apply(
        classify,
        axis=1
    )

    print(
        pair_df[
            [
                "code_a",
                "code_b",
                "station_names",
                "total_gap_occurrences",
                "affected_trains",
                "review_priority"
            ]
        ]
        .sort_values(
            [
                "total_gap_occurrences",
                "code_a"
            ],
            ascending=[False, True]
        )
        .head(50)
        .to_string(index=False)
    )

else:

    print("No candidates available.")


# ============================================================
# 12. FIND AMBIGUOUS NORMALIZED-NAME GROUPS
# ============================================================

print("\n" + "=" * 80)
print("AMBIGUOUS STATION NAME GROUPS")
print("=" * 80)

ambiguous_groups = []

for normalized_name, group in stations.groupby(
    "normalized_name"
):

    codes = sorted(
        group["station_code"].unique()
    )

    names = sorted(
        group["station_name"].unique()
    )

    if len(codes) > 1:

        ambiguous_groups.append({
            "normalized_name": normalized_name,
            "codes": " | ".join(codes),
            "station_names": " | ".join(names),
            "number_of_codes": len(codes)
        })


ambiguous_df = pd.DataFrame(
    ambiguous_groups
)

if len(ambiguous_df) > 0:

    ambiguous_df = ambiguous_df.sort_values(
        [
            "number_of_codes",
            "normalized_name"
        ],
        ascending=[False, True]
    )

    print(
        ambiguous_df.head(50).to_string(
            index=False
        )
    )

else:

    print("No ambiguous groups found.")


# ============================================================
# 13. SAVE OUTPUT FILES
# ============================================================

print("\n" + "=" * 80)
print("SAVING OUTPUT FILES")
print("=" * 80)


if len(pair_df) > 0:

    pair_df.to_csv(
        OUTPUT_EXACT,
        index=False
    )

    print(
        f"✅ Saved: {OUTPUT_EXACT}"
    )

else:

    # Save empty file with headers
    pd.DataFrame(
        columns=[
            "normalized_name",
            "code_a",
            "code_b",
            "station_names",
            "number_of_codes",
            "code_pair",
            "total_gap_occurrences",
            "affected_trains",
            "review_priority"
        ]
    ).to_csv(
        OUTPUT_EXACT,
        index=False
    )

    print(
        f"✅ Saved empty candidate file: "
        f"{OUTPUT_EXACT}"
    )


ambiguous_df.to_csv(
    OUTPUT_AMBIGUOUS,
    index=False
)

print(
    f"✅ Saved: {OUTPUT_AMBIGUOUS}"
)


gap_summary.to_csv(
    OUTPUT_GAPS,
    index=False
)

print(
    f"✅ Saved: {OUTPUT_GAPS}"
)


# ============================================================
# 14. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("STEP 3C SUMMARY")
print("=" * 80)

print(
    f"Unique station codes: "
    f"{stations['station_code'].nunique()}"
)

print(
    f"Unique station names: "
    f"{stations['station_name'].nunique()}"
)

print(
    f"Names with multiple codes: "
    f"{len(candidate_names)}"
)

print(
    f"Candidate code pairs: "
    f"{len(pair_df)}"
)

print(
    f"Exact-name code variations found in gaps: "
    f"{len(gap_summary)}"
)

print(
    f"Total route gaps analyzed: "
    f"{len(gap_df)}"
)

print("\nIMPORTANT:")
print(
    "⚠️ No station codes were changed in Dataset 1."
)

print(
    "⚠️ These are candidate mappings for review only."
)

print(
    "⚠️ Same station name does NOT automatically mean "
    "same physical railway station."
)

print(
    "✅ Original ml_ready_segments.csv remains unchanged."
)

print("\nStep 3C completed.")