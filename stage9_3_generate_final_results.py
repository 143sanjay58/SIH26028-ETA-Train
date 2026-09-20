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
# CONFIGURATION
# ============================================================

INPUT_FILE = "stage9_1d_continuous_simulation_results.csv"

OUTPUT_FILE = "stage9_dynamic_eta_results.csv"


# ============================================================
# START
# ============================================================

print("=" * 70)
print("STAGE 9.3 - FINAL DYNAMIC ETA RESULTS GENERATION")
print("=" * 70)


# ============================================================
# LOAD STAGE 9.1D RESULTS
# ============================================================

print("\n[1] Loading Stage 9.1D simulation results...")

df = pd.read_csv(INPUT_FILE)

print(
    f"[1] Loaded {len(df)} simulation updates."
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "step",
    "train_number",
    "route_position",
    "current_station",
    "current_time",
    "arrival_delay",
    "departure_delay",
    "upcoming_station_count",
    "first_upcoming_station",
    "first_eta",
    "first_remaining_minutes",
    "eta_changed"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    raise ValueError(
        "Missing columns: "
        + ", ".join(missing_columns)
    )


print(
    "✓ Required columns verified."
)


# ============================================================
# CREATE FINAL DATASET
# ============================================================

print("\n[2] Preparing final dynamic ETA dataset...")


final_df = df[required_columns].copy()


# Convert time columns

final_df["current_time"] = pd.to_datetime(
    final_df["current_time"]
)

final_df["first_eta"] = pd.to_datetime(
    final_df["first_eta"]
)


# Calculate actual predicted duration

final_df["calculated_remaining_minutes"] = (
    (
        final_df["first_eta"]
        - final_df["current_time"]
    ).dt.total_seconds()
    / 60.0
)


# Calculate delay change

final_df["arrival_delay_change"] = (
    final_df["arrival_delay"]
    .diff()
    .fillna(0)
)


# ============================================================
# VALIDATE CALCULATED REMAINING TIME
# ============================================================

print(
    "\n[3] Validating ETA / remaining-time consistency..."
)


difference = (
    final_df["calculated_remaining_minutes"]
    - final_df["first_remaining_minutes"]
).abs()


max_difference = difference.max()


print(
    f"Maximum difference: "
    f"{max_difference:.6f} minutes"
)


if max_difference > 0.01:

    raise ValueError(
        "ETA and remaining-time values "
        "are inconsistent."
    )


print(
    "✓ ETA and remaining-time values are consistent."
)


# ============================================================
# VALIDATE ROW COUNT
# ============================================================

if len(final_df) != len(df):

    raise ValueError(
        "Final dataset row count changed."
    )


print(
    f"✓ Row count preserved: {len(final_df)}"
)


# ============================================================
# VALIDATE DUPLICATES
# ============================================================

duplicate_count = final_df.duplicated().sum()


print(
    f"Duplicate rows: {duplicate_count}"
)


if duplicate_count != 0:

    raise ValueError(
        "Duplicate rows found."
    )


print(
    "✓ No duplicate rows."
)


# ============================================================
# SAVE FINAL DATASET
# ============================================================

print(
    "\n[4] Saving final dynamic ETA results..."
)


final_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"✓ Final dataset saved: {OUTPUT_FILE}"
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL DYNAMIC ETA DATASET SUMMARY")
print("=" * 70)


print(
    f"Simulation updates : {len(final_df)}"
)

print(
    f"Train number       : "
    f"{final_df['train_number'].iloc[0]}"
)

print(
    f"Position range     : "
    f"{final_df['route_position'].min()} "
    f"→ "
    f"{final_df['route_position'].max()}"
)

print(
    f"Delay range        : "
    f"{final_df['arrival_delay'].min():.0f} "
    f"→ "
    f"{final_df['arrival_delay'].max():.0f} min"
)

print(
    f"Remaining-time range: "
    f"{final_df['first_remaining_minutes'].min():.2f} "
    f"→ "
    f"{final_df['first_remaining_minutes'].max():.2f} min"
)

print(
    f"ETA changes        : "
    f"{final_df['eta_changed'].sum()}"
)


# ============================================================
# FINAL CHECK
# ============================================================

print("\n" + "=" * 70)

print(
    "STAGE 9.3: PASS"
)

print("=" * 70)