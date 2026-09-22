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
import numpy as np


# ============================================================
# STEP 3E
# STATION CODE TIME & ROUTE BEHAVIOR VALIDATION
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

OUTPUT_FILE = "station_code_time_validation.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("STEP 3E - STATION CODE TIME & ROUTE BEHAVIOR VALIDATION")
print("=" * 80)

df = pd.read_csv(DATASET1_PATH)

print("\nDataset loaded")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# PRESERVE ROUTE ORDER
# ============================================================

df["route_order"] = (
    df.groupby("train_number")
    .cumcount() + 1
)


# ============================================================
# PREVIOUS SEGMENT INFORMATION
# ============================================================

df["previous_to_station"] = (
    df.groupby("train_number")["to_station"]
    .shift(1)
)

df["previous_to_station_name"] = (
    df.groupby("train_number")["to_station_name"]
    .shift(1)
)

df["previous_to_departure"] = (
    df.groupby("train_number")["to_departure"]
    .shift(1)
)

df["previous_to_day"] = (
    df.groupby("train_number")["to_day"]
    .shift(1)
)


# ============================================================
# TIME CONVERSION
# ============================================================

def time_to_minutes(value):

    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    if value.lower() in ["nan", "none", ""]:
        return np.nan

    try:

        parts = value.split(":")

        hour = int(parts[0])
        minute = int(parts[1])

        return hour * 60 + minute

    except:

        return np.nan


df["previous_departure_minutes"] = (
    df["previous_to_departure"]
    .apply(time_to_minutes)
)

df["current_arrival_minutes"] = (
    df["from_arrival"]
    .apply(time_to_minutes)
)


# ============================================================
# ABSOLUTE TIME
# ============================================================

df["previous_departure_absolute"] = (
    df["previous_to_day"] * 1440
    +
    df["previous_departure_minutes"]
)

df["current_arrival_absolute"] = (
    df["from_day"] * 1440
    +
    df["current_arrival_minutes"]
)


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def analyze_direction(data, code_a, code_b, direction):

    print("\n" + "-" * 80)
    print(f"{code_a} -> {code_b}")
    print("-" * 80)

    print(
        "Transitions found:",
        len(data)
    )

    if len(data) == 0:
        return None, data


    # --------------------------------------------------------
    # Calculate scheduled transition time
    # --------------------------------------------------------

    data = data.copy()

    data["transition_minutes"] = (
        data["current_arrival_absolute"]
        -
        data["previous_departure_absolute"]
    )


    # --------------------------------------------------------
    # Remove impossible negative values
    # --------------------------------------------------------

    valid = data[
        data["transition_minutes"].notna()
        &
        (data["transition_minutes"] >= 0)
    ].copy()


    print(
        "Transitions with valid timestamps:",
        len(valid)
    )


    if len(valid) == 0:

        print("❌ No valid timestamp calculations")

        return None, data


    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print(
        f"Minimum: "
        f"{valid['transition_minutes'].min():.0f} min"
    )

    print(
        f"Maximum: "
        f"{valid['transition_minutes'].max():.0f} min"
    )

    print(
        f"Average: "
        f"{valid['transition_minutes'].mean():.2f} min"
    )

    print(
        f"Median: "
        f"{valid['transition_minutes'].median():.2f} min"
    )


    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    zero_to_2 = (
        valid["transition_minutes"] <= 2
    ).sum()

    zero_to_5 = (
        valid["transition_minutes"] <= 5
    ).sum()

    greater_5 = (
        valid["transition_minutes"] > 5
    ).sum()

    greater_15 = (
        valid["transition_minutes"] > 15
    ).sum()

    greater_30 = (
        valid["transition_minutes"] > 30
    ).sum()


    print("\nTime distribution:")

    print(
        f"  0-2 min  : {zero_to_2}"
    )

    print(
        f"  0-5 min  : {zero_to_5}"
    )

    print(
        f"  >5 min   : {greater_5}"
    )

    print(
        f"  >15 min  : {greater_15}"
    )

    print(
        f"  >30 min  : {greater_30}"
    )


    # --------------------------------------------------------
    # Percentage near zero
    # --------------------------------------------------------

    near_zero_percentage = (
        zero_to_5
        /
        len(valid)
        *
        100
    )

    print(
        f"\n0-5 minute percentage: "
        f"{near_zero_percentage:.2f}%"
    )


    # --------------------------------------------------------
    # Show examples
    # --------------------------------------------------------

    print("\nSample transitions:")

    display_columns = [
        "train_number",
        "route_order",
        "previous_to_station",
        "previous_to_departure",
        "previous_to_day",
        "from_station",
        "from_arrival",
        "from_day",
        "transition_minutes"
    ]

    print(
        valid[
            display_columns
        ]
        .head(10)
        .to_string(index=False)
    )


    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "code_a": code_a,

        "code_b": code_b,

        "direction": direction,

        "transition_count":
            len(data),

        "valid_time_count":
            len(valid),

        "min_minutes":
            valid["transition_minutes"].min(),

        "max_minutes":
            valid["transition_minutes"].max(),

        "mean_minutes":
            valid["transition_minutes"].mean(),

        "median_minutes":
            valid["transition_minutes"].median(),

        "zero_to_2_count":
            zero_to_2,

        "zero_to_5_count":
            zero_to_5,

        "greater_5_count":
            greater_5,

        "greater_15_count":
            greater_15,

        "greater_30_count":
            greater_30,

        "zero_to_5_percentage":
            near_zero_percentage
    }


    return result, valid


# ============================================================
# ANALYZE ALL CANDIDATES
# ============================================================

results = []

all_details = []


for code_a, code_b in CANDIDATE_PAIRS:

    print("\n\n")
    print("=" * 80)
    print(
        f"VALIDATING: {code_a} <-> {code_b}"
    )
    print("=" * 80)


    # ========================================================
    # A -> B
    # ========================================================

    a_to_b = df[
        (df["previous_to_station"] == code_a)
        &
        (df["from_station"] == code_b)
    ].copy()


    result, details = analyze_direction(
        a_to_b,
        code_a,
        code_b,
        f"{code_a}->{code_b}"
    )


    if result is not None:
        results.append(result)


    if len(details) > 0:

        details = details.copy()

        details["code_a"] = code_a
        details["code_b"] = code_b
        details["direction"] = (
            f"{code_a}->{code_b}"
        )

        all_details.append(details)


    # ========================================================
    # B -> A
    # ========================================================

    b_to_a = df[
        (df["previous_to_station"] == code_b)
        &
        (df["from_station"] == code_a)
    ].copy()


    result, details = analyze_direction(
        b_to_a,
        code_b,
        code_a,
        f"{code_b}->{code_a}"
    )


    if result is not None:
        results.append(result)


    if len(details) > 0:

        details = details.copy()

        details["code_a"] = code_b
        details["code_b"] = code_a
        details["direction"] = (
            f"{code_b}->{code_a}"
        )

        all_details.append(details)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n\n")
print("=" * 80)
print("FINAL TIME VALIDATION SUMMARY")
print("=" * 80)


if len(results) > 0:

    results_df = pd.DataFrame(results)

    print(
        results_df.to_string(
            index=False
        )
    )

else:

    results_df = pd.DataFrame()

    print("No valid results.")


# ============================================================
# SAVE SUMMARY
# ============================================================

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SAVE DETAILED DATA
# ============================================================

if len(all_details) > 0:

    details_df = pd.concat(
        all_details,
        ignore_index=True
    )

    details_df.to_csv(
        "station_code_time_validation_details.csv",
        index=False
    )

    print(
        "\n✅ Detailed transition data saved:"
    )

    print(
        "station_code_time_validation_details.csv"
    )


print("\n" + "=" * 80)
print("OUTPUT")
print("=" * 80)

print(
    f"✅ Summary saved: {OUTPUT_FILE}"
)

print(
    "\n⚠️ No station codes were changed."
)

print(
    "⚠️ This is analysis only."
)

print(
    "✅ ml_ready_segments.csv remains unchanged."
)

print("\nStep 3E completed.")