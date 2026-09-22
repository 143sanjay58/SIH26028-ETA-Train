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

from train_state import TrainState
from dynamic_eta_engine import DynamicETAEngine


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_NUMBER = "12303"

DATASET_PATH = "ml_ready_segments_final.csv"

SIMULATED_POSITIONS = [2, 3, 4, 5, 6, 10, 20]

ARRIVAL_DELAYS = [15, 16, 19, 17, 20, 22, 18]

DEPARTURE_DELAYS = [17, 18, 21, 19, 22, 24, 20]

TIME_OFFSETS_MINUTES = [0, 3, 7, 11, 15, 28, 48]

START_TIME = datetime(2024, 9, 26, 8, 17)


# ============================================================
# LOAD TRAIN ROUTE
# ============================================================

def load_train_route():

    print("    Loading Dataset 1 for station mapping...")

    route = pd.read_csv(DATASET_PATH)

    print(
        f"    Dataset 1 loaded: {len(route)} rows"
    )

    train_route = route[
        route["train_number"].astype(str) == TRAIN_NUMBER
    ].copy()

    if train_route.empty:

        raise ValueError(
            f"Train {TRAIN_NUMBER} not found in Dataset 1."
        )

    train_route = train_route.sort_values(
        "route_order"
    ).reset_index(drop=True)

    print(
        f"    Train {TRAIN_NUMBER} route rows: "
        f"{len(train_route)}"
    )

    return train_route


# ============================================================
# CREATE SIMULATED TRAIN STATES
# ============================================================

def create_simulated_states():

    states = []

    for i, position in enumerate(SIMULATED_POSITIONS):

        current_time = (
            START_TIME
            + timedelta(
                minutes=TIME_OFFSETS_MINUTES[i]
            )
        )

        state = TrainState(
            train_number=TRAIN_NUMBER,
            current_station="",
            current_route_position=position,
            current_arrival_delay=ARRIVAL_DELAYS[i],
            current_departure_delay=DEPARTURE_DELAYS[i],
            current_time=current_time
        )

        states.append(state)

    return states


# ============================================================
# ASSIGN CURRENT STATIONS
# ============================================================

def assign_current_stations(
    states,
    train_route
):

    for state in states:

        matching_rows = train_route[
            train_route["route_order"]
            == state.current_route_position
        ]

        if matching_rows.empty:

            raise ValueError(
                f"No route found for position "
                f"{state.current_route_position}"
            )

        state.current_station = str(
            matching_rows.iloc[0]["from_station"]
        )


# ============================================================
# FIND STATION FROM ENGINE RESULT
# ============================================================

def get_station_from_result(
    result
):
    """
    Extract station information without assuming
    a single dictionary key.

    This makes the simulation compatible with the
    existing DynamicETAEngine output.
    """

    possible_keys = [
        "station",
        "target_station",
        "target_station_code",
        "station_code",
        "to_station",
        "current_station"
    ]

    for key in possible_keys:

        if key in result:

            value = result[key]

            if value is not None:

                return str(value)

    return "UNKNOWN"


# ============================================================
# FIND REMAINING TIME
# ============================================================

def get_remaining_time(
    result
):
    """
    Extract predicted remaining time from the
    existing ETA engine result.
    """

    possible_keys = [
        "predicted_remaining_minutes",
        "remaining_minutes",
        "predicted_remaining_time",
        "remaining_time"
    ]

    for key in possible_keys:

        if key in result:

            value = result[key]

            if value is not None:

                return float(value)

    raise KeyError(
        "Could not find predicted remaining time "
        "in ETA engine result."
    )


# ============================================================
# FIND ETA
# ============================================================

def get_eta(
    result
):
    """
    Extract ETA from the existing ETA engine result.
    """

    possible_keys = [
        "eta",
        "predicted_eta",
        "estimated_arrival_time",
        "arrival_time"
    ]

    for key in possible_keys:

        if key in result:

            value = result[key]

            if value is not None:

                # Already a datetime
                if isinstance(
                    value,
                    datetime
                ):
                    return value

                # Convert string representation
                return pd.to_datetime(
                    value
                ).to_pydatetime()

    raise KeyError(
        "Could not find ETA in ETA engine result."
    )


# ============================================================
# VALIDATE ETA RESULTS
# ============================================================

def validate_eta_results(
    state,
    results
):

    if not isinstance(
        results,
        list
    ):

        raise AssertionError(
            "ETA engine result is not a list."
        )

    if len(results) == 0:

        raise AssertionError(
            f"No upcoming stations returned for "
            f"position {state.current_route_position}."
        )

    previous_eta = None

    for result in results:

        # ----------------------------------------------------
        # Remaining time
        # ----------------------------------------------------

        remaining = get_remaining_time(
            result
        )

        if remaining < 0:

            raise AssertionError(
                "Negative predicted remaining time detected."
            )

        # ----------------------------------------------------
        # ETA
        # ----------------------------------------------------

        eta = get_eta(
            result
        )

        if eta < state.current_time:

            raise AssertionError(
                f"ETA occurs before current time: {eta}"
            )

        # ----------------------------------------------------
        # ETA ordering
        # ----------------------------------------------------

        if previous_eta is not None:

            if eta < previous_eta:

                raise AssertionError(
                    "ETA sequence is not monotonic."
                )

        previous_eta = eta


# ============================================================
# DISPLAY PREDICTION
# ============================================================

def display_prediction(
    prediction
):

    station = get_station_from_result(
        prediction
    )

    remaining = get_remaining_time(
        prediction
    )

    eta = get_eta(
        prediction
    )

    print(
        f"    {station:<10}"
        f" | ETA: {eta}"
        f" | Remaining: {remaining:.2f} min"
    )


# ============================================================
# MAIN SIMULATION
# ============================================================

def main():

    print("=" * 70)
    print("STAGE 9.1C - DYNAMIC ETA SIMULATION")
    print("=" * 70)

    print()
    print(
        f"Train: {TRAIN_NUMBER}"
    )

    print(
        "Simulation positions:",
        SIMULATED_POSITIONS
    )

    # ========================================================
    # STEP 1
    # ========================================================

    print()
    print("[1] Loading Dynamic ETA Engine...")

    eta_engine = DynamicETAEngine()

    print(
        "    Dynamic ETA Engine loaded successfully."
    )

    # ========================================================
    # STEP 2
    # ========================================================

    print()
    print("[2] Loading train route...")

    train_route = load_train_route()

    # ========================================================
    # STEP 3
    # ========================================================

    print()
    print("[3] Creating simulated train states...")

    states = create_simulated_states()

    print(
        f"    Created {len(states)} simulated states."
    )

    # ========================================================
    # STEP 4
    # ========================================================

    print()
    print("[4] Assigning current stations...")

    assign_current_stations(
        states,
        train_route
    )

    for state in states:

        print(
            f"    Position "
            f"{state.current_route_position:>3}"
            f" | Station "
            f"{state.current_station:<6}"
            f" | Time "
            f"{state.current_time}"
            f" | Arrival Delay "
            f"{state.current_arrival_delay:>3}"
            f" | Departure Delay "
            f"{state.current_departure_delay:>3}"
        )

    # ========================================================
    # STEP 5
    # RUN DYNAMIC ETA PREDICTIONS
    # ========================================================

    print()
    print("[5] Running dynamic ETA predictions...")

    previous_upcoming_count = None

    first_upcoming_etas = []

    all_state_results = []

    for index, state in enumerate(
        states,
        start=1
    ):

        print()
        print("-" * 70)

        print(
            f"SIMULATION STATE {index}"
        )

        print(
            f"Current position : "
            f"{state.current_route_position}"
        )

        print(
            f"Current station  : "
            f"{state.current_station}"
        )

        print(
            f"Current time     : "
            f"{state.current_time}"
        )

        print(
            f"Arrival delay    : "
            f"{state.current_arrival_delay} min"
        )

        print(
            f"Departure delay  : "
            f"{state.current_departure_delay} min"
        )

        # ----------------------------------------------------
        # RUN ENGINE
        # ----------------------------------------------------

        results = eta_engine.update_state(
            state
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        validate_eta_results(
            state,
            results
        )

        # Save complete results
        all_state_results.append(
            results
        )

        # ----------------------------------------------------
        # UPCOMING STATION COUNT
        # ----------------------------------------------------

        upcoming_count = len(
            results
        )

        if previous_upcoming_count is not None:

            if upcoming_count >= previous_upcoming_count:

                raise AssertionError(
                    "Upcoming station count did not decrease "
                    "as the train moved forward."
                )

        previous_upcoming_count = (
            upcoming_count
        )

        # ----------------------------------------------------
        # FIRST UPCOMING ETA
        # ----------------------------------------------------

        first_prediction = results[0]

        first_eta = get_eta(
            first_prediction
        )

        first_remaining = get_remaining_time(
            first_prediction
        )

        first_station = get_station_from_result(
            first_prediction
        )

        first_upcoming_etas.append(
            first_eta
        )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        print()

        print(
            f"Upcoming stations: "
            f"{upcoming_count}"
        )

        print(
            f"First upcoming station: "
            f"{first_station}"
        )

        print(
            f"First predicted ETA: "
            f"{first_eta}"
        )

        print(
            f"First predicted remaining: "
            f"{first_remaining:.2f} min"
        )

        # ----------------------------------------------------
        # FIRST 3 PREDICTIONS
        # ----------------------------------------------------

        print()

        print(
            "First 3 upcoming predictions:"
        )

        for prediction in results[:3]:

            display_prediction(
                prediction
            )

    # ========================================================
    # STEP 6
    # DYNAMIC RECALCULATION CHECK
    # ========================================================

    print()
    print("=" * 70)
    print("DYNAMIC ETA RECALCULATION CHECK")
    print("=" * 70)

    eta_changed = False

    for i in range(
        1,
        len(first_upcoming_etas)
    ):

        previous_eta = (
            first_upcoming_etas[i - 1]
        )

        current_eta = (
            first_upcoming_etas[i]
        )

        if current_eta != previous_eta:

            eta_changed = True

            print(
                f"State {i} -> State {i + 1}: "
                f"ETA changed"
            )

            print(
                f"    Previous ETA: "
                f"{previous_eta}"
            )

            print(
                f"    Current ETA : "
                f"{current_eta}"
            )

    if not eta_changed:

        raise AssertionError(
            "ETA did not change between simulation states."
        )

    print()
    print(
        "Dynamic ETA recalculation detected successfully."
    )

    # ========================================================
    # STEP 7
    # DELAY MOVEMENT CHECK
    # ========================================================

    print()
    print("=" * 70)
    print("DYNAMIC DELAY CHECK")
    print("=" * 70)

    delay_changed = False

    for i in range(
        1,
        len(states)
    ):

        previous_delay = (
            states[i - 1].current_arrival_delay
        )

        current_delay = (
            states[i].current_arrival_delay
        )

        if current_delay != previous_delay:

            delay_changed = True

            difference = (
                current_delay
                - previous_delay
            )

            print(
                f"State {i} -> State {i + 1}: "
                f"Arrival delay "
                f"{previous_delay} -> "
                f"{current_delay} "
                f"({difference:+d} min)"
            )

    if not delay_changed:

        raise AssertionError(
            "Simulated train delay never changed."
        )

    print()
    print(
        "Dynamic delay movement verified."
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print()
    print("=" * 70)
    print("STAGE 9.1C VALIDATION")
    print("=" * 70)

    print()
    print("✓ Train states created")

    print(
        "✓ Current stations assigned correctly"
    )

    print(
        "✓ Dynamic ETA Engine executed"
    )

    print(
        "✓ ETA generated for upcoming stations"
    )

    print(
        "✓ Predicted remaining time is non-negative"
    )

    print(
        "✓ ETA is not before current time"
    )

    print(
        "✓ ETA sequence is monotonic"
    )

    print(
        "✓ Upcoming station count decreases"
    )

    print(
        "✓ ETA changes dynamically"
    )

    print(
        "✓ Train delay changes during simulation"
    )

    print()
    print("=" * 70)
    print("STAGE 9.1C: PASS")
    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()