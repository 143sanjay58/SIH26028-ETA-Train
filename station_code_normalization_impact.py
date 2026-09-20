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
# STEP 3F
# STATION CODE NORMALIZATION - IMPACT ANALYSIS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"

OUTPUT_FILE = "station_code_normalization_impact.csv"


# ============================================================
# PROPOSED MAPPINGS
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
print("STEP 3F - STATION CODE NORMALIZATION IMPACT ANALYSIS")
print("=" * 80)

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("✅ Dataset loaded")

print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# ORIGINAL BASIC STATISTICS
# ============================================================

original_unique_from = df["from_station"].nunique()
original_unique_to = df["to_station"].nunique()

original_unique_codes = len(
    set(df["from_station"].dropna())
    |
    set(df["to_station"].dropna())
)

original_unique_names = len(
    set(df["from_station_name"].dropna())
    |
    set(df["to_station_name"].dropna())
)


print("\n" + "=" * 80)
print("ORIGINAL DATASET")
print("=" * 80)

print(
    "Unique from_station codes:",
    original_unique_from
)

print(
    "Unique to_station codes:",
    original_unique_to
)

print(
    "Unique station codes overall:",
    original_unique_codes
)

print(
    "Unique station names overall:",
    original_unique_names
)


# ============================================================
# IMPACT ANALYSIS FOR EACH MAPPING
# ============================================================

results = []


for old_code, new_code in MAPPINGS.items():

    print("\n")
    print("=" * 80)
    print(
        f"ANALYZING {old_code} -> {new_code}"
    )
    print("=" * 80)


    # --------------------------------------------------------
    # FROM-STATION occurrences
    # --------------------------------------------------------

    from_count = (
        df["from_station"]
        == old_code
    ).sum()


    # --------------------------------------------------------
    # TO-STATION occurrences
    # --------------------------------------------------------

    to_count = (
        df["to_station"]
        == old_code
    ).sum()


    total_occurrences = (
        from_count
        +
        to_count
    )


    # --------------------------------------------------------
    # Affected trains
    # --------------------------------------------------------

    affected_from_trains = set(
        df.loc[
            df["from_station"] == old_code,
            "train_number"
        ]
    )

    affected_to_trains = set(
        df.loc[
            df["to_station"] == old_code,
            "train_number"
        ]
    )

    affected_trains = (
        affected_from_trains
        |
        affected_to_trains
    )


    # --------------------------------------------------------
    # Rows affected
    # --------------------------------------------------------

    affected_rows = df[
        (df["from_station"] == old_code)
        |
        (df["to_station"] == old_code)
    ].copy()


    print(
        f"\n{old_code} occurrences:"
    )

    print(
        "  from_station:",
        from_count
    )

    print(
        "  to_station:",
        to_count
    )

    print(
        "  total:",
        total_occurrences
    )

    print(
        "  affected rows:",
        len(affected_rows)
    )

    print(
        "  affected trains:",
        len(affected_trains)
    )


    # --------------------------------------------------------
    # Station names associated with old code
    # --------------------------------------------------------

    from_names = set(
        df.loc[
            df["from_station"] == old_code,
            "from_station_name"
        ].dropna()
    )

    to_names = set(
        df.loc[
            df["to_station"] == old_code,
            "to_station_name"
        ].dropna()
    )

    old_names = (
        from_names
        |
        to_names
    )


    print(
        "\nNames associated with",
        old_code,
        ":"
    )

    for name in sorted(old_names):
        print(
            " ",
            name
        )


    # --------------------------------------------------------
    # New code statistics
    # --------------------------------------------------------

    new_from_count = (
        df["from_station"]
        == new_code
    ).sum()

    new_to_count = (
        df["to_station"]
        == new_code
    ).sum()

    new_total = (
        new_from_count
        +
        new_to_count
    )


    print(
        f"\nExisting {new_code} occurrences:"
    )

    print(
        "  from_station:",
        new_from_count
    )

    print(
        "  to_station:",
        new_to_count
    )

    print(
        "  total:",
        new_total
    )


    # --------------------------------------------------------
    # Train overlap
    # --------------------------------------------------------

    old_trains = affected_trains

    new_from_trains = set(
        df.loc[
            df["from_station"] == new_code,
            "train_number"
        ]
    )

    new_to_trains = set(
        df.loc[
            df["to_station"] == new_code,
            "train_number"
        ]
    )

    new_trains = (
        new_from_trains
        |
        new_to_trains
    )


    overlap = (
        old_trains
        &
        new_trains
    )


    print(
        "\nTrain usage:"
    )

    print(
        f"  {old_code} trains:",
        len(old_trains)
    )

    print(
        f"  {new_code} trains:",
        len(new_trains)
    )

    print(
        "  trains using BOTH:",
        len(overlap)
    )


    # --------------------------------------------------------
    # Sample affected trains
    # --------------------------------------------------------

    print(
        "\nSample affected trains:"
    )

    sample_trains = sorted(
        affected_trains,
        key=str
    )[:20]

    print(
        sample_trains
    )


    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    results.append({

        "old_code":
            old_code,

        "new_code":
            new_code,

        "old_occurrences":
            total_occurrences,

        "old_from_occurrences":
            from_count,

        "old_to_occurrences":
            to_count,

        "affected_rows":
            len(affected_rows),

        "affected_trains":
            len(affected_trains),

        "new_occurrences":
            new_total,

        "new_trains":
            len(new_trains),

        "train_overlap":
            len(overlap),

        "old_names":
            " | ".join(
                sorted(old_names)
            )
    })


# ============================================================
# SIMULATE NORMALIZATION
# ============================================================

print("\n")
print("=" * 80)
print("SIMULATING NORMALIZATION")
print("=" * 80)

simulated = df.copy()


simulated["from_station"] = (
    simulated["from_station"]
    .replace(MAPPINGS)
)

simulated["to_station"] = (
    simulated["to_station"]
    .replace(MAPPINGS)
)


# ============================================================
# AFTER STATISTICS
# ============================================================

after_unique_from = (
    simulated["from_station"]
    .nunique()
)

after_unique_to = (
    simulated["to_station"]
    .nunique()
)

after_unique_codes = len(
    set(simulated["from_station"].dropna())
    |
    set(simulated["to_station"].dropna())
)


print(
    "\nUnique from_station codes BEFORE:",
    original_unique_from
)

print(
    "Unique from_station codes AFTER :",
    after_unique_from
)

print(
    "\nUnique to_station codes BEFORE:",
    original_unique_to
)

print(
    "Unique to_station codes AFTER :",
    after_unique_to
)

print(
    "\nUnique station codes BEFORE:",
    original_unique_codes
)

print(
    "Unique station codes AFTER :",
    after_unique_codes
)

print(
    "\nCodes reduced by:",
    original_unique_codes
    -
    after_unique_codes
)


# ============================================================
# CHECK FOR NEW SAME-STATION SEGMENTS
# ============================================================

simulated_same_station = (
    simulated["from_station"]
    ==
    simulated["to_station"]
).sum()


original_same_station = (
    df["from_station"]
    ==
    df["to_station"]
).sum()


print("\n" + "=" * 80)
print("SAME-STATION CHECK")
print("=" * 80)

print(
    "Same-station rows BEFORE:",
    original_same_station
)

print(
    "Same-station rows AFTER :",
    simulated_same_station
)

print(
    "New same-station rows created:",
    simulated_same_station
    -
    original_same_station
)


# ============================================================
# CHECK FOR ROUTE SEGMENT CHANGES
# ============================================================

original_segments = (
    df[
        [
            "train_number",
            "from_station",
            "to_station"
        ]
    ]
    .astype(str)
)

simulated_segments = (
    simulated[
        [
            "train_number",
            "from_station",
            "to_station"
        ]
    ]
    .astype(str)
)


segment_changed = (
    original_segments
    != simulated_segments
).any(axis=1)


print("\n" + "=" * 80)
print("ROUTE SEGMENT IMPACT")
print("=" * 80)

print(
    "Rows whose station codes change:",
    segment_changed.sum()
)


# ============================================================
# CHECK FOR EXACT DUPLICATE SEGMENTS
# ============================================================

original_duplicate_segments = (
    df[
        [
            "train_number",
            "from_station",
            "to_station"
        ]
    ]
    .duplicated()
    .sum()
)

simulated_duplicate_segments = (
    simulated[
        [
            "train_number",
            "from_station",
            "to_station"
        ]
    ]
    .duplicated()
    .sum()
)


print(
    "\nDuplicate route segments BEFORE:",
    original_duplicate_segments
)

print(
    "Duplicate route segments AFTER :",
    simulated_duplicate_segments
)


# ============================================================
# FINAL SUMMARY TABLE
# ============================================================

results_df = pd.DataFrame(results)


print("\n")
print("=" * 80)
print("PAIR-WISE IMPACT SUMMARY")
print("=" * 80)

print(
    results_df.to_string(
        index=False
    )
)


# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n")
print("=" * 80)
print("OUTPUT")
print("=" * 80)

print(
    f"✅ Saved: {OUTPUT_FILE}"
)

print(
    "\n⚠️ Original ml_ready_segments.csv was NOT modified."
)

print(
    "⚠️ Normalization has NOT been applied."
)

print(
    "\nStep 3F completed."
)