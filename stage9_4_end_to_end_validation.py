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

INPUT_FILE = "stage9_dynamic_eta_results.csv"


# ============================================================
# START
# ============================================================

print("=" * 70)
print("STAGE 9.4 - FINAL END-TO-END VALIDATION")
print("=" * 70)


# ============================================================
# 1. LOAD FINAL RESULTS
# ============================================================

print("\n[1] Loading final dynamic ETA results...")

df = pd.read_csv(INPUT_FILE)

print(
    f"✓ Results loaded: {len(df)} updates"
)


# ============================================================
# 2. REQUIRED PIPELINE OUTPUTS
# ============================================================

print("\n[2] Checking required pipeline outputs...")

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
    "eta_changed",
    "calculated_remaining_minutes",
    "arrival_delay_change"
]


missing = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing:
    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing)
    )


print("✓ All required pipeline outputs are present.")


# ============================================================
# 3. BASIC DATA VALIDATION
# ============================================================

print("\n[3] Performing basic data validation...")


if df.empty:
    raise ValueError("Final dataset is empty.")


if df["train_number"].nunique() != 1:
    raise ValueError(
        "Multiple train numbers found."
    )


if df["route_position"].isna().any():
    raise ValueError(
        "Missing route positions found."
    )


if df["current_station"].isna().any():
    raise ValueError(
        "Missing current stations found."
    )


print("✓ Basic data validation passed.")


# ============================================================
# 4. TRAIN MOVEMENT VALIDATION
# ============================================================

print("\n[4] Validating train movement...")


positions = df["route_position"].tolist()


for i in range(1, len(positions)):

    if positions[i] <= positions[i - 1]:

        raise ValueError(
            "Train did not move forward."
        )


print(
    f"✓ Train moved forward: "
    f"{positions[0]} → {positions[-1]}"
)


# ============================================================
# 5. UPCOMING STATION VALIDATION
# ============================================================

print("\n[5] Validating upcoming stations...")


upcoming_counts = (
    df["upcoming_station_count"]
    .tolist()
)


for i in range(1, len(upcoming_counts)):

    if upcoming_counts[i] >= upcoming_counts[i - 1]:

        raise ValueError(
            "Upcoming station count did not decrease."
        )


print(
    f"✓ Upcoming stations decreased: "
    f"{upcoming_counts[0]} → {upcoming_counts[-1]}"
)


# ============================================================
# 6. REMAINING TIME VALIDATION
# ============================================================

print("\n[6] Validating predicted remaining time...")


remaining = (
    df["first_remaining_minutes"]
)


if remaining.isna().any():
    raise ValueError(
        "Missing remaining-time predictions."
    )


if (remaining < 0).any():
    raise ValueError(
        "Negative remaining-time prediction found."
    )


print(
    f"✓ Remaining time is non-negative."
)

print(
    f"  Range: "
    f"{remaining.min():.2f} → "
    f"{remaining.max():.2f} minutes"
)


# ============================================================
# 7. ETA VALIDATION
# ============================================================

print("\n[7] Validating ETA values...")


df["current_time"] = pd.to_datetime(
    df["current_time"]
)

df["first_eta"] = pd.to_datetime(
    df["first_eta"]
)


if (df["first_eta"] < df["current_time"]).any():

    raise ValueError(
        "ETA occurs before current train time."
    )


print(
    "✓ Every ETA is at or after current train time."
)


# ============================================================
# 8. ETA / REMAINING TIME CONSISTENCY
# ============================================================

print(
    "\n[8] Checking ETA and remaining-time consistency..."
)


calculated = (
    (
        df["first_eta"]
        - df["current_time"]
    )
    .dt.total_seconds()
    / 60.0
)


difference = (
    calculated
    - df["first_remaining_minutes"]
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
# 9. DYNAMIC ETA VALIDATION
# ============================================================

print("\n[9] Validating dynamic ETA behaviour...")


eta_changes = df["eta_changed"]


if eta_changes.sum() == 0:

    raise ValueError(
        "ETA never changed during simulation."
    )


print(
    f"✓ ETA changed in "
    f"{int(eta_changes.sum())}/"
    f"{len(df)} updates."
)


# ============================================================
# 10. DELAY VARIATION VALIDATION
# ============================================================

print("\n[10] Validating dynamic delay behaviour...")


delay_range = (
    df["arrival_delay"].max()
    - df["arrival_delay"].min()
)


if delay_range <= 0:

    raise ValueError(
        "Train delay did not change."
    )


print(
    f"✓ Train delay changed dynamically."
)

print(
    f"  Delay range: "
    f"{df['arrival_delay'].min():.0f} → "
    f"{df['arrival_delay'].max():.0f} minutes"
)


# ============================================================
# 11. FIRST UPCOMING STATION MOVEMENT
# ============================================================

print(
    "\n[11] Checking upcoming station movement..."
)


stations = (
    df["first_upcoming_station"]
    .tolist()
)


for i in range(1, len(stations)):

    if stations[i] == stations[i - 1]:

        raise ValueError(
            "First upcoming station did not change."
        )


print(
    "✓ First upcoming station changed "
    "as train moved forward."
)


# ============================================================
# 12. PIPELINE COMPLETENESS
# ============================================================

print(
    "\n[12] Checking end-to-end pipeline completeness..."
)


pipeline_checks = {

    "Train state present":
        df["current_station"].notna().all(),

    "Route position present":
        df["route_position"].notna().all(),

    "Delay state present":
        df["arrival_delay"].notna().all(),

    "Upcoming stations generated":
        df["upcoming_station_count"].notna().all(),

    "ETA generated":
        df["first_eta"].notna().all(),

    "Remaining time generated":
        df["first_remaining_minutes"].notna().all(),

    "Dynamic ETA observed":
        df["eta_changed"].sum() > 0
}


for check, result in pipeline_checks.items():

    if not result:
        raise ValueError(
            f"Pipeline check failed: {check}"
        )

    print(
        f"✓ {check}"
    )


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)
print("STAGE 9.4 FINAL VALIDATION SUMMARY")
print("=" * 70)


print(
    f"Train                 : "
    f"{df['train_number'].iloc[0]}"
)

print(
    f"Simulation updates    : "
    f"{len(df)}"
)

print(
    f"Route movement        : "
    f"{positions[0]} → {positions[-1]}"
)

print(
    f"Upcoming stations     : "
    f"{upcoming_counts[0]} → "
    f"{upcoming_counts[-1]}"
)

print(
    f"Delay range           : "
    f"{df['arrival_delay'].min():.0f} → "
    f"{df['arrival_delay'].max():.0f} min"
)

print(
    f"Remaining-time range  : "
    f"{remaining.min():.2f} → "
    f"{remaining.max():.2f} min"
)

print(
    f"ETA changes           : "
    f"{int(eta_changes.sum())}/{len(df)}"
)

print(
    f"Maximum ETA difference: "
    f"{max_difference:.6f} min"
)


print("\n" + "=" * 70)
print("STAGE 9.4: PASS")
print("=" * 70)
print("STAGE 9: COMPLETE")
print("=" * 70)