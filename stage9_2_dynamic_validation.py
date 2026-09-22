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


# ============================================================
# START
# ============================================================

print("=" * 70)
print("STAGE 9.2 - DYNAMIC BEHAVIOUR VALIDATION")
print("=" * 70)


# ============================================================
# LOAD RESULTS
# ============================================================

print("\n[1] Loading Stage 9.1D results...")

df = pd.read_csv(INPUT_FILE)

print(
    f"[1] Results loaded: {len(df)} updates"
)


# ============================================================
# BASIC CHECK
# ============================================================

if df.empty:
    raise ValueError(
        "ERROR: Simulation results are empty."
    )


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


for column in required_columns:

    if column not in df.columns:

        raise ValueError(
            f"ERROR: Missing column: {column}"
        )


print(
    "✓ Required columns are present"
)


# ============================================================
# VALIDATION 1
# FORWARD TRAIN MOVEMENT
# ============================================================

print("\n[2] Checking forward train movement...")

positions = df[
    "route_position"
].tolist()

forward_movement = all(
    positions[i] > positions[i - 1]
    for i in range(1, len(positions))
)


if not forward_movement:

    raise ValueError(
        "ERROR: Train did not move forward."
    )


print(
    f"✓ Train positions: {positions}"
)

print(
    "✓ Forward movement validation: PASS"
)


# ============================================================
# VALIDATION 2
# UPCOMING STATIONS DECREASE
# ============================================================

print(
    "\n[3] Checking upcoming station count..."
)

station_counts = df[
    "upcoming_station_count"
].tolist()


station_count_decreasing = all(
    station_counts[i] < station_counts[i - 1]
    for i in range(1, len(station_counts))
)


if not station_count_decreasing:

    raise ValueError(
        "ERROR: Upcoming station count "
        "did not decrease."
    )


print(
    f"✓ Upcoming station counts: "
    f"{station_counts}"
)

print(
    "✓ Upcoming station validation: PASS"
)


# ============================================================
# VALIDATION 3
# REMAINING TIME
# ============================================================

print(
    "\n[4] Checking remaining prediction time..."
)

remaining_values = pd.to_numeric(
    df["first_remaining_minutes"],
    errors="coerce"
)


if remaining_values.isna().any():

    raise ValueError(
        "ERROR: Invalid remaining-time value."
    )


negative_remaining = (
    remaining_values < 0
).sum()


if negative_remaining > 0:

    raise ValueError(
        "ERROR: Negative remaining-time "
        "prediction found."
    )


print(
    f"✓ Minimum remaining time: "
    f"{remaining_values.min():.2f} min"
)

print(
    f"✓ Maximum remaining time: "
    f"{remaining_values.max():.2f} min"
)

print(
    "✓ Remaining-time validation: PASS"
)


# ============================================================
# VALIDATION 4
# ETA VALIDITY
# ============================================================

print(
    "\n[5] Checking ETA validity..."
)


current_times = pd.to_datetime(
    df["current_time"],
    errors="coerce"
)


eta_values = pd.to_datetime(
    df["first_eta"],
    errors="coerce"
)


if current_times.isna().any():

    raise ValueError(
        "ERROR: Invalid current_time."
    )


if eta_values.isna().any():

    raise ValueError(
        "ERROR: Invalid ETA value."
    )


eta_before_current = (
    eta_values < current_times
).sum()


if eta_before_current > 0:

    raise ValueError(
        "ERROR: ETA occurs before current time."
    )


print(
    "✓ All ETA values are at or after "
    "current train time"
)

print(
    "✓ ETA validity validation: PASS"
)


# ============================================================
# VALIDATION 5
# ETA CHANGES DYNAMICALLY
# ============================================================

print(
    "\n[6] Checking dynamic ETA changes..."
)


eta_changed_values = df[
    "eta_changed"
].astype(str).str.lower()


dynamic_changes = (
    eta_changed_values == "true"
).sum()


if dynamic_changes < 2:

    raise ValueError(
        "ERROR: ETA did not change enough "
        "during simulation."
    )


print(
    f"✓ ETA changed in "
    f"{dynamic_changes}/{len(df)} updates"
)

print(
    "✓ Dynamic ETA change validation: PASS"
)


# ============================================================
# VALIDATION 6
# TRAIN DELAY CHANGES
# ============================================================

print(
    "\n[7] Checking train delay changes..."
)


arrival_delays = df[
    "arrival_delay"
].tolist()


departure_delays = df[
    "departure_delay"
].tolist()


arrival_changed = len(
    set(arrival_delays)
) > 1


departure_changed = len(
    set(departure_delays)
) > 1


if not arrival_changed:

    raise ValueError(
        "ERROR: Arrival delay never changed."
    )


if not departure_changed:

    raise ValueError(
        "ERROR: Departure delay never changed."
    )


print(
    f"✓ Arrival delays: {arrival_delays}"
)

print(
    f"✓ Departure delays: {departure_delays}"
)

print(
    "✓ Delay-change validation: PASS"
)


# ============================================================
# VALIDATION 7
# FIRST UPCOMING STATION CHANGES
# ============================================================

print(
    "\n[8] Checking upcoming station movement..."
)


stations = df[
    "first_upcoming_station"
].tolist()


station_changed = len(
    set(stations)
) > 1


if not station_changed:

    raise ValueError(
        "ERROR: First upcoming station "
        "never changed."
    )


print(
    f"✓ First upcoming stations: {stations}"
)

print(
    "✓ Upcoming-station movement validation: PASS"
)


# ============================================================
# DYNAMIC RELATIONSHIP CHECK
# ============================================================

print(
    "\n[9] Checking dynamic relationship..."
)


delay_variation = (
    max(arrival_delays)
    - min(arrival_delays)
)


eta_variation = (
    eta_values.max()
    - eta_values.min()
)


print(
    f"✓ Arrival-delay variation: "
    f"{delay_variation:.2f} min"
)

print(
    f"✓ ETA variation: "
    f"{eta_variation}"
)


if delay_variation <= 0:

    raise ValueError(
        "ERROR: No delay variation detected."
    )


if eta_variation.total_seconds() <= 0:

    raise ValueError(
        "ERROR: No ETA variation detected."
    )


print(
    "✓ Dynamic relationship validation: PASS"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("STAGE 9.2 FINAL VALIDATION")
print("=" * 70)


print(
    "✓ Forward train movement"
)

print(
    "✓ Upcoming station count decreases"
)

print(
    "✓ Remaining time is non-negative"
)

print(
    "✓ ETA is not before current time"
)

print(
    "✓ ETA changes dynamically"
)

print(
    "✓ Train delays change dynamically"
)

print(
    "✓ Upcoming stations change correctly"
)

print(
    "✓ Dynamic ETA behaviour confirmed"
)


print("\n" + "=" * 70)

print(
    "STAGE 9.2: PASS"
)

print("=" * 70)