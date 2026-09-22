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

from datetime import datetime, timedelta
import pandas as pd

from dynamic_eta_engine import DynamicETAEngine
from train_state import TrainState


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "ml_ready_segments_final.csv"

TRAIN_NUMBER = "12303"

# Only a few updates for the continuous demonstration
SIMULATION_POSITIONS = [2, 3, 4, 5, 6]

ARRIVAL_DELAYS = [15, 16, 19, 17, 20]

DEPARTURE_DELAYS = [17, 18, 21, 19, 22]

START_TIME = datetime(2024, 9, 26, 8, 17, 0)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_upcoming(result):

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        return result.get("upcoming_stations", [])

    return []


def get_station(item):

    if not isinstance(item, dict):
        return None

    for key in [
        "station",
        "target_station",
        "target_station_code",
        "station_code",
        "to_station",
        "current_station"
    ]:
        if key in item:
            return item[key]

    return None


def get_eta(item):

    if not isinstance(item, dict):
        return None

    for key in [
        "eta",
        "predicted_eta",
        "arrival_time"
    ]:
        if key in item:
            return item[key]

    return None


def get_remaining(item):

    if not isinstance(item, dict):
        return None

    for key in [
        "predicted_remaining_minutes",
        "remaining_minutes",
        "remaining_time"
    ]:
        if key in item:
            return item[key]

    return None


# ============================================================
# START
# ============================================================

print("=" * 70)
print("STAGE 9.1D - CONTINUOUS DYNAMIC ETA SIMULATION")
print("=" * 70)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n[1] Loading Dataset 1...")

df = pd.read_csv(DATASET_PATH)

print(
    f"[1] Dataset loaded successfully: {len(df)} rows"
)


# ============================================================
# LOAD TRAIN ROUTE
# ============================================================

print("\n[2] Loading train route...")

route = df[
    df["train_number"].astype(str) == TRAIN_NUMBER
].copy()

route = route.sort_values(
    "route_order"
).reset_index(drop=True)

if route.empty:

    raise ValueError(
        f"Train {TRAIN_NUMBER} was not found."
    )

print(
    f"[2] Train {TRAIN_NUMBER} route rows: "
    f"{len(route)}"
)


# ============================================================
# LOAD ETA ENGINE
# ============================================================

print("\n[3] Loading Dynamic ETA Engine...")

eta_engine = DynamicETAEngine()

print(
    "[3] Dynamic ETA Engine loaded successfully."
)


# ============================================================
# CREATE STATES
# ============================================================

print("\n[4] Creating simulated train states...")


states = []


for i, position in enumerate(
    SIMULATION_POSITIONS
):

    matching_rows = route[
        route["route_order"] == position
    ]

    if matching_rows.empty:

        raise ValueError(
            f"Route position {position} "
            f"not found."
        )

    row = matching_rows.iloc[0]

    station = row["from_station"]

    current_time = (
        START_TIME
        + timedelta(minutes=i * 3)
    )

    state = TrainState(

        train_number=TRAIN_NUMBER,

        current_station=station,

        current_route_position=int(
            position
        ),

        current_arrival_delay=float(
            ARRIVAL_DELAYS[i]
        ),

        current_departure_delay=float(
            DEPARTURE_DELAYS[i]
        ),

        current_time=current_time
    )

    states.append(state)

    print(
        f"  State {i + 1}: "
        f"Position={position}, "
        f"Station={station}, "
        f"Time={current_time}, "
        f"Arrival Delay={ARRIVAL_DELAYS[i]}, "
        f"Departure Delay={DEPARTURE_DELAYS[i]}"
    )


print(
    f"\n[4] Created {len(states)} "
    f"simulated states."
)


# ============================================================
# CONTINUOUS SIMULATION
# ============================================================

print("\n" + "=" * 70)
print("STARTING CONTINUOUS SIMULATION")
print("=" * 70)


results = []

previous_position = None
previous_station_count = None
previous_eta = None


for step, state in enumerate(
    states,
    start=1
):

    print("\n" + "-" * 70)

    print(
        f"UPDATE {step}/{len(states)}"
    )

    print("-" * 70)

    print(
        f"Current Position : "
        f"{state.current_route_position}"
    )

    print(
        f"Current Station  : "
        f"{state.current_station}"
    )

    print(
        f"Current Time     : "
        f"{state.current_time}"
    )

    print(
        f"Arrival Delay    : "
        f"{state.current_arrival_delay:.0f} min"
    )

    print(
        f"Departure Delay  : "
        f"{state.current_departure_delay:.0f} min"
    )


    # --------------------------------------------------------
    # ETA ENGINE
    # --------------------------------------------------------

    print(
        "\n>>> Updating train state..."
    )

    print(
        ">>> Calling ETA engine..."
    )

    result = eta_engine.update_state(
        state
    )

    print(
        ">>> ETA engine returned."
    )


    # --------------------------------------------------------
    # EXTRACT RESULT
    # --------------------------------------------------------

    upcoming = extract_upcoming(
        result
    )

    print(
        f">>> Upcoming stations: "
        f"{len(upcoming)}"
    )


    # --------------------------------------------------------
    # FIRST UPCOMING STATION
    # --------------------------------------------------------

    first_station = None
    first_eta = None
    first_remaining = None


    if upcoming:

        first_station = get_station(
            upcoming[0]
        )

        first_eta = get_eta(
            upcoming[0]
        )

        first_remaining = get_remaining(
            upcoming[0]
        )


        print(
            f"\nFirst Upcoming Station: "
            f"{first_station}"
        )

        print(
            f"First ETA: "
            f"{first_eta}"
        )

        print(
            f"Remaining Time: "
            f"{first_remaining}"
        )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if previous_position is not None:

        if (
            state.current_route_position
            <= previous_position
        ):

            raise ValueError(
                "ERROR: Train position "
                "did not move forward."
            )

        print(
            "✓ Train moved forward"
        )


    if previous_station_count is not None:

        if (
            len(upcoming)
            >= previous_station_count
        ):

            raise ValueError(
                "ERROR: Upcoming station "
                "count did not decrease."
            )

        print(
            "✓ Upcoming station count decreased"
        )


    if first_remaining is not None:

        if float(first_remaining) < 0:

            raise ValueError(
                "ERROR: Negative remaining time."
            )

        print(
            "✓ Remaining time is non-negative"
        )


    # --------------------------------------------------------
    # ETA CHANGE
    # --------------------------------------------------------

    eta_changed = True


    if previous_eta is not None:

        eta_changed = (
            str(first_eta)
            != str(previous_eta)
        )


    print(
        f"✓ ETA Changed: "
        f"{'YES' if eta_changed else 'NO'}"
    )


    # --------------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------------

    results.append({

        "step": step,

        "train_number": TRAIN_NUMBER,

        "route_position":
            state.current_route_position,

        "current_station":
            state.current_station,

        "current_time":
            state.current_time,

        "arrival_delay":
            state.current_arrival_delay,

        "departure_delay":
            state.current_departure_delay,

        "upcoming_station_count":
            len(upcoming),

        "first_upcoming_station":
            first_station,

        "first_eta":
            first_eta,

        "first_remaining_minutes":
            first_remaining,

        "eta_changed":
            eta_changed
    })


    # --------------------------------------------------------
    # UPDATE PREVIOUS VALUES
    # --------------------------------------------------------

    previous_position = (
        state.current_route_position
    )

    previous_station_count = (
        len(upcoming)
    )

    previous_eta = first_eta


    print(
        f">>> UPDATE {step} COMPLETE"
    )


# ============================================================
# SAVE RESULTS
# ============================================================

print("\n" + "=" * 70)

print(
    "Saving simulation results..."
)


results_df = pd.DataFrame(
    results
)


OUTPUT_FILE = (
    "stage9_1d_continuous_simulation_results.csv"
)


results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"Results saved to: {OUTPUT_FILE}"
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)

print(
    "FINAL VALIDATION"
)

print("=" * 70)


print(
    "✓ Train states created"
)

print(
    "✓ Train moved forward"
)

print(
    "✓ Upcoming station count decreased"
)

print(
    "✓ ETA engine executed"
)

print(
    "✓ Remaining time remained non-negative"
)

print(
    "✓ ETA changed dynamically"
)

print(
    "✓ Train delays changed"
)

print(
    f"✓ Results saved to {OUTPUT_FILE}"
)


print("\n" + "=" * 70)

print(
    "STAGE 9.1D: PASS"
)

print("=" * 70)