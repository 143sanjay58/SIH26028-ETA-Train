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
# STAGE 9.1 — DYNAMIC TRAIN STATE SIMULATOR
# ============================================================


# ============================================================
# 1. CONFIGURATION
# ============================================================

DATASET_PATH = "ml_ready_segments_final.csv"

TRAIN_NUMBER = "12303"

# Route positions that we want to simulate
SIMULATION_POSITIONS = [2, 3, 4, 5, 6, 10, 20]

# Simulated changing delay values
SIMULATED_ARRIVAL_DELAYS = [
    15,
    16,
    19,
    17,
    20,
    22,
    18
]

SIMULATED_DEPARTURE_DELAYS = [
    17,
    18,
    21,
    19,
    22,
    24,
    20
]


# ============================================================
# 2. LOAD FROZEN DATASET
# ============================================================

print("Loading Dataset 1...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print("Rows:", len(df))


# ============================================================
# 3. NORMALIZE TRAIN NUMBER
# ============================================================

df["train_number"] = (
    df["train_number"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 4. GET TRAIN ROUTE
# ============================================================

train_route = df[
    df["train_number"] == TRAIN_NUMBER
].copy()


# ============================================================
# 5. CHECK TRAIN EXISTS
# ============================================================

if train_route.empty:

    raise ValueError(
        f"Train {TRAIN_NUMBER} was not found in Dataset 1."
    )


# Sort route correctly
train_route = train_route.sort_values(
    "route_order"
).reset_index(drop=True)


print()
print("Train:", TRAIN_NUMBER)
print("Route segments:", len(train_route))

print(
    "Maximum route position:",
    train_route["route_order"].max()
)


# ============================================================
# 6. DISPLAY FIRST 10 ROUTE POSITIONS
# ============================================================

print()
print("First 10 route positions:")
print()

print(
    train_route[
        [
            "route_order",
            "from_station",
            "from_station_name",
            "to_station",
            "to_station_name"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ============================================================
# 7. VALIDATE SIMULATION CONFIGURATION
# ============================================================

if len(SIMULATION_POSITIONS) != len(
    SIMULATED_ARRIVAL_DELAYS
):

    raise ValueError(
        "Number of positions and arrival delays do not match."
    )


if len(SIMULATION_POSITIONS) != len(
    SIMULATED_DEPARTURE_DELAYS
):

    raise ValueError(
        "Number of positions and departure delays do not match."
    )


# ============================================================
# 8. GENERATE DYNAMIC TRAIN STATES
# ============================================================

simulated_states = []


for i, position in enumerate(
    SIMULATION_POSITIONS
):

    # Find the exact route segment
    row = train_route[
        train_route["route_order"] == position
    ]


    # Position doesn't exist
    if row.empty:

        print(
            f"Position {position} not found. Skipping."
        )

        continue


    # Get first matching row
    row = row.iloc[0]


    # Create train state
    state = {

        "train_number": TRAIN_NUMBER,

        "current_station": str(
            row["from_station"]
        ),

        "current_station_name": str(
            row["from_station_name"]
        ),

        "current_route_position": int(
            row["route_order"]
        ),

        "next_station": str(
            row["to_station"]
        ),

        "next_station_name": str(
            row["to_station_name"]
        ),

        "current_arrival_delay": float(
            SIMULATED_ARRIVAL_DELAYS[i]
        ),

        "current_departure_delay": float(
            SIMULATED_DEPARTURE_DELAYS[i]
        )
    }


    simulated_states.append(state)


# ============================================================
# 9. DISPLAY GENERATED STATES
# ============================================================

print()
print("Dynamic simulated train states:")
print()

for state in simulated_states:

    print(
        f"Position {state['current_route_position']:>3} | "
        f"{state['current_station']:<5} "
        f"({state['current_station_name']:<20}) | "
        f"Next: {state['next_station']:<5} | "
        f"Arrival delay: "
        f"{state['current_arrival_delay']:>5.1f} min | "
        f"Departure delay: "
        f"{state['current_departure_delay']:>5.1f} min"
    )


# ============================================================
# 10. VALIDATION — POSITIONS
# ============================================================

positions_generated = [

    state["current_route_position"]

    for state in simulated_states
]


# Check positions are increasing
if positions_generated != sorted(
    positions_generated
):

    raise ValueError(
        "Generated route positions are not increasing."
    )


# Check duplicate positions
if len(positions_generated) != len(
    set(positions_generated)
):

    raise ValueError(
        "Duplicate route positions detected."
    )


# ============================================================
# 11. VALIDATION — STATIONS
# ============================================================

for state in simulated_states:

    position = state[
        "current_route_position"
    ]

    station = state[
        "current_station"
    ]


    row = train_route[
        train_route["route_order"] == position
    ]


    if row.empty:

        raise ValueError(
            f"Route position {position} does not exist."
        )


    expected_station = str(
        row.iloc[0]["from_station"]
    )


    if station != expected_station:

        raise ValueError(

            f"Station-position mismatch at "
            f"position {position}: "
            f"{station} != {expected_station}"

        )


# ============================================================
# 12. VALIDATION — DELAYS
# ============================================================

for state in simulated_states:

    if state["current_arrival_delay"] < 0:

        raise ValueError(
            "Negative arrival delay detected."
        )


    if state["current_departure_delay"] < 0:

        raise ValueError(
            "Negative departure delay detected."
        )


# ============================================================
# 13. CHECK THAT DELAY ACTUALLY CHANGES
# ============================================================

arrival_delays = [

    state["current_arrival_delay"]

    for state in simulated_states
]


departure_delays = [

    state["current_departure_delay"]

    for state in simulated_states
]


arrival_changed = (
    len(set(arrival_delays)) > 1
)


departure_changed = (
    len(set(departure_delays)) > 1
)


if not arrival_changed:

    raise ValueError(
        "Arrival delay is not changing."
    )


if not departure_changed:

    raise ValueError(
        "Departure delay is not changing."
    )


# ============================================================
# 14. SHOW DELAY MOVEMENT
# ============================================================

print()
print("Delay movement:")
print()

for i in range(
    1,
    len(simulated_states)
):

    previous = simulated_states[i - 1]
    current = simulated_states[i]


    arrival_change = (
        current["current_arrival_delay"]
        -
        previous["current_arrival_delay"]
    )


    departure_change = (
        current["current_departure_delay"]
        -
        previous["current_departure_delay"]
    )


    print(
        f"{previous['current_station']} "
        f"→ "
        f"{current['current_station']} | "

        f"Arrival delay change: "
        f"{arrival_change:+.1f} min | "

        f"Departure delay change: "
        f"{departure_change:+.1f} min"
    )


# ============================================================
# 15. FINAL VALIDATION
# ============================================================

print()
print("Validation checks:")
print()

print("✓ Train exists")
print("✓ Route positions are valid")
print("✓ Route positions are increasing")
print("✓ No duplicate positions")
print("✓ Station-position relationships are valid")
print("✓ No negative arrival delays")
print("✓ No negative departure delays")
print("✓ Delay values change during simulation")


# ============================================================
# 16. FINAL RESULT
# ============================================================

print()
print("========================================")
print("Stage 9.1B Dynamic Delay Simulation: PASS")
print("========================================")