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
# STEP 3D - STATION CODE CANDIDATE VALIDATION
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"

CANDIDATE_PAIRS = [
    ("SBI", "SBT"),
    ("CGKP", "CGKR"),
    ("GDPL", "GOPL"),
    ("BMKI", "MKI"),
    ("KWAE", "KWF"),
    ("BTJL", "BTKL"),
    ("SRN", "SRNK"),
    ("CDLD", "CLDY"),
]

OUTPUT_FILE = "station_code_validation_results.csv"


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("=" * 80)
print("STEP 3D - STATION CODE CANDIDATE VALIDATION")
print("=" * 80)

print("\nLoading Dataset 1...")

df = pd.read_csv(DATASET1_PATH)

print("✅ Dataset 1 loaded")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 2. PRESERVE ROUTE ORDER
# ============================================================

df["route_order"] = (
    df.groupby("train_number")
    .cumcount() + 1
)


# ============================================================
# 3. CREATE PREVIOUS STATION INFORMATION
# ============================================================

df["previous_to_station"] = (
    df.groupby("train_number")["to_station"]
    .shift(1)
)

df["previous_to_station_name"] = (
    df.groupby("train_number")["to_station_name"]
    .shift(1)
)


# ============================================================
# 4. VALIDATE EACH CANDIDATE
# ============================================================

results = []


for code_a, code_b in CANDIDATE_PAIRS:

    print("\n")
    print("=" * 80)
    print(f"VALIDATING: {code_a} <-> {code_b}")
    print("=" * 80)

    # --------------------------------------------------------
    # All segments involving either code
    # --------------------------------------------------------

    involved = df[
        df["from_station"].isin([code_a, code_b])
        |
        df["to_station"].isin([code_a, code_b])
    ].copy()

    # --------------------------------------------------------
    # Count usage
    # --------------------------------------------------------

    from_a = (
        df["from_station"] == code_a
    ).sum()

    to_a = (
        df["to_station"] == code_a
    ).sum()

    from_b = (
        df["from_station"] == code_b
    ).sum()

    to_b = (
        df["to_station"] == code_b
    ).sum()

    trains_a = set(
        df.loc[
            (df["from_station"] == code_a)
            |
            (df["to_station"] == code_a),
            "train_number"
        ]
    )

    trains_b = set(
        df.loc[
            (df["from_station"] == code_b)
            |
            (df["to_station"] == code_b),
            "train_number"
        ]
    )

    common_trains = trains_a.intersection(
        trains_b
    )

    # --------------------------------------------------------
    # Direct A -> B and B -> A transitions
    # --------------------------------------------------------

    a_to_b = df[
        (df["previous_to_station"] == code_a)
        &
        (df["from_station"] == code_b)
    ].copy()

    b_to_a = df[
        (df["previous_to_station"] == code_b)
        &
        (df["from_station"] == code_a)
    ].copy()

    # --------------------------------------------------------
    # Same-name gap check
    # --------------------------------------------------------

    same_name_ab = a_to_b[
        a_to_b["previous_to_station_name"]
        ==
        a_to_b["from_station_name"]
    ]

    same_name_ba = b_to_a[
        b_to_a["previous_to_station_name"]
        ==
        b_to_a["from_station_name"]
    ]

    # --------------------------------------------------------
    # Display station names
    # --------------------------------------------------------

    names_a = sorted(
        set(
            involved.loc[
                (
                    involved["from_station"]
                    == code_a
                ),
                "from_station_name"
            ].dropna()
        )
        |
        set(
            involved.loc[
                (
                    involved["to_station"]
                    == code_a
                ),
                "to_station_name"
            ].dropna()
        )
    )

    names_b = sorted(
        set(
            involved.loc[
                (
                    involved["from_station"]
                    == code_b
                ),
                "from_station_name"
            ].dropna()
        )
        |
        set(
            involved.loc[
                (
                    involved["to_station"]
                    == code_b
                ),
                "to_station_name"
            ].dropna()
        )
    )

    # --------------------------------------------------------
    # Print analysis
    # --------------------------------------------------------

    print("\nStation names:")
    print(f"  {code_a}: {names_a}")
    print(f"  {code_b}: {names_b}")

    print("\nUsage:")
    print(f"  {code_a} as FROM station: {from_a}")
    print(f"  {code_a} as TO station:   {to_a}")
    print(f"  {code_b} as FROM station: {from_b}")
    print(f"  {code_b} as TO station:   {to_b}")

    print("\nTrain usage:")
    print(f"  Trains using {code_a}: {len(trains_a)}")
    print(f"  Trains using {code_b}: {len(trains_b)}")
    print(f"  Trains using BOTH:     {len(common_trains)}")

    print("\nDirect route transitions:")
    print(f"  {code_a} -> {code_b}: {len(a_to_b)}")
    print(f"  {code_b} -> {code_a}: {len(b_to_a)}")

    print("\nSame-name direct gaps:")
    print(
        f"  {code_a} -> {code_b}: "
        f"{len(same_name_ab)}"
    )
    print(
        f"  {code_b} -> {code_a}: "
        f"{len(same_name_ba)}"
    )

    # --------------------------------------------------------
    # Show common trains
    # --------------------------------------------------------

    if len(common_trains) > 0:

        print("\nSample trains using BOTH codes:")

        sample_common = sorted(
            list(common_trains),
            key=str
        )[:20]

        print(
            sample_common
        )

    else:

        print(
            "\nNo train uses both codes."
        )

    # --------------------------------------------------------
    # Show direct transition examples
    # --------------------------------------------------------

    if len(a_to_b) > 0:

        print(
            f"\nSample {code_a} -> {code_b} transitions:"
        )

        print(
            a_to_b[
                [
                    "train_number",
                    "route_order",
                    "previous_to_station",
                    "previous_to_station_name",
                    "from_station",
                    "from_station_name"
                ]
            ]
            .head(10)
            .to_string(index=False)
        )

    if len(b_to_a) > 0:

        print(
            f"\nSample {code_b} -> {code_a} transitions:"
        )

        print(
            b_to_a[
                [
                    "train_number",
                    "route_order",
                    "previous_to_station",
                    "previous_to_station_name",
                    "from_station",
                    "from_station_name"
                ]
            ]
            .head(10)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # Save result summary
    # --------------------------------------------------------

    results.append({

        "code_a": code_a,

        "code_b": code_b,

        "names_a": " | ".join(
            map(str, names_a)
        ),

        "names_b": " | ".join(
            map(str, names_b)
        ),

        "code_a_total_usage":
            from_a + to_a,

        "code_b_total_usage":
            from_b + to_b,

        "trains_using_code_a":
            len(trains_a),

        "trains_using_code_b":
            len(trains_b),

        "common_train_count":
            len(common_trains),

        "a_to_b_transitions":
            len(a_to_b),

        "b_to_a_transitions":
            len(b_to_a),

        "same_name_a_to_b":
            len(same_name_ab),

        "same_name_b_to_a":
            len(same_name_ba),

    })


# ============================================================
# 5. SUMMARY TABLE
# ============================================================

results_df = pd.DataFrame(results)

print("\n")
print("=" * 80)
print("FINAL VALIDATION SUMMARY")
print("=" * 80)

print(
    results_df.to_string(
        index=False
    )
)


# ============================================================
# 6. SAVE RESULTS
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
    "\n⚠️ No station codes were modified."
)

print(
    "⚠️ This step is analysis only."
)

print(
    "✅ Original ml_ready_segments.csv remains unchanged."
)

print("\nStep 3D completed.")