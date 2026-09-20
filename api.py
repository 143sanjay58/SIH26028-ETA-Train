from datetime import datetime

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from train_state import TrainState
from dynamic_eta_engine import DynamicETAEngine
from eta_response import build_eta_response

from passenger_request import PassengerRequest
from passenger_assistance_engine import create_assistance_response

from role_api import router as role_router


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SIH Dynamic Train ETA API",
    description="Dynamic ETA prediction system for coaching trains",
    version="1.0.0"
)

# Allow the Vite dashboard (localhost:5173 / 127.0.0.1:5173)
# to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Role-based endpoints: /login, /logout, /copilot/...,
# /control-room/..., /train/{train_number}/status
app.include_router(role_router)


# ============================================================
# REQUEST MODEL
# ============================================================

class ETARequest(BaseModel):

    train_number: str

    current_station: str

    current_route_position: int

    current_arrival_delay: float

    current_departure_delay: float

    current_time: datetime


# ============================================================
# PASSENGER ASSISTANCE REQUEST MODEL
# ============================================================

class PassengerAssistanceRequest(BaseModel):

    train_number: str

    boarding_station: str

    destination_station: str

    current_route_position: int

    current_arrival_delay: float

    current_departure_delay: float

    current_time: datetime


# ============================================================
# LOAD FROZEN ROUTE DATA
# ============================================================

ROUTE_FILE = "ml_ready_segments_final.csv"

try:

    route_data = pd.read_csv(ROUTE_FILE)

    route_data["train_number"] = (
        route_data["train_number"]
        .astype(str)
        .str.strip()
    )

    route_data["current_route_position"] = (
        route_data["route_order"]
        .astype(int)
    )

    print("Frozen route dataset loaded successfully.")

except Exception as e:

    route_data = None

    print("WARNING: Route dataset loading failed:")
    print(e)


# ============================================================
# INITIALIZE ETA ENGINE
# ============================================================

try:

    eta_engine = DynamicETAEngine()

    print("Dynamic ETA Engine initialized successfully.")

except Exception as e:

    eta_engine = None

    print("WARNING: ETA Engine initialization failed:")
    print(e)


# ============================================================
# ROUTE VALIDATION FUNCTION
# ============================================================

def validate_train_state(request: ETARequest):

    """
    Validates railway-domain consistency:

    1. Train exists.
    2. Route position is within the train route.
    3. Station exists in the train route.
    4. Station matches the supplied route position.
    """

    if route_data is None:

        raise HTTPException(
            status_code=500,
            detail="Route dataset is not available."
        )


    # --------------------------------------------------------
    # Basic route-position validation
    # --------------------------------------------------------

    if request.current_route_position < 1:

        raise HTTPException(
            status_code=400,
            detail="Route position must be >= 1."
        )


    # --------------------------------------------------------
    # Get the requested train route
    # --------------------------------------------------------

    train_route = route_data[
        route_data["train_number"] == request.train_number
    ].copy()


    if train_route.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Train {request.train_number} "
                "not found in Dataset 1."
            )
        )


    train_route = train_route.sort_values(
        "route_order"
    )


    # --------------------------------------------------------
    # Check route-position range
    # --------------------------------------------------------

    minimum_position = int(
        train_route["route_order"].min()
    )

    maximum_position = int(
        train_route["route_order"].max()
    ) + 1


    if request.current_route_position > maximum_position:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid route position "
                f"{request.current_route_position}. "
                f"Valid positions for train "
                f"{request.train_number} are "
                f"{minimum_position} to {maximum_position}."
            )
        )


    # --------------------------------------------------------
    # Normalize supplied station code
    # --------------------------------------------------------

    requested_station = (
        request.current_station
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # Build station-position mapping
    #
    # route_order N:
    #   from_station = position N
    #   to_station   = position N + 1
    # --------------------------------------------------------

    station_positions = {}

    for _, row in train_route.iterrows():

        route_position = int(row["route_order"])

        from_station = str(
            row["from_station"]
        ).strip().upper()

        from_station_canonical = str(
            row["from_station_canonical"]
        ).strip().upper()

        to_station = str(
            row["to_station"]
        ).strip().upper()

        to_station_canonical = str(
            row["to_station_canonical"]
        ).strip().upper()


        station_positions.setdefault(
            route_position,
            set()
        ).update(
            [
                from_station,
                from_station_canonical
            ]
        )


        station_positions.setdefault(
            route_position + 1,
            set()
        ).update(
            [
                to_station,
                to_station_canonical
            ]
        )


    # --------------------------------------------------------
    # Check whether station belongs to this train
    # --------------------------------------------------------

    matching_positions = [

        position

        for position, station_codes
        in station_positions.items()

        if requested_station in station_codes

    ]


    if not matching_positions:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Station {requested_station} "
                f"does not belong to train "
                f"{request.train_number}."
            )
        )


    # --------------------------------------------------------
    # Check station-position consistency
    # --------------------------------------------------------

    valid_station_codes = station_positions.get(
        request.current_route_position,
        set()
    )


    if requested_station not in valid_station_codes:

        expected_station = sorted(
            valid_station_codes
        )

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Station and route position do not match.",
                "train_number": request.train_number,
                "provided_station": requested_station,
                "provided_route_position":
                    request.current_route_position,
                "expected_station_codes":
                    expected_station,
                "station_positions_found":
                    matching_positions
            }
        )


# ============================================================
# PASSENGER REQUEST VALIDATION
# ============================================================

def validate_passenger_request(
    request: PassengerAssistanceRequest
):

    """
    Validates passenger-specific information.

    For Stage 10.8, the boarding station represents
    the current station of the train.
    """

    boarding_station = (
        request.boarding_station
        .strip()
        .upper()
    )

    destination_station = (
        request.destination_station
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # Boarding station validation
    # --------------------------------------------------------

    if not boarding_station:

        raise HTTPException(
            status_code=400,
            detail="Boarding station cannot be empty."
        )


    # --------------------------------------------------------
    # Destination validation
    # --------------------------------------------------------

    if not destination_station:

        raise HTTPException(
            status_code=400,
            detail="Destination station cannot be empty."
        )


    # --------------------------------------------------------
    # Boarding station cannot equal destination
    # --------------------------------------------------------

    if boarding_station == destination_station:

        raise HTTPException(
            status_code=400,
            detail=(
                "Boarding station and destination station "
                "cannot be the same."
            )
        )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {

        "status": "success",

        "project":
            "SIH Dynamic Train ETA",

        "message":
            "Dynamic ETA API is running.",

        "endpoint":
            "/predict-eta",

        "passenger_endpoint":
            "/passenger-assistance"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "eta_engine_loaded":
            eta_engine is not None,

        "route_dataset_loaded":
            route_data is not None
    }


# ============================================================
# ETA PREDICTION ENDPOINT
# ============================================================

@app.post("/predict-eta")
def predict_eta(request: ETARequest):

    # --------------------------------------------------------
    # Check ETA engine
    # --------------------------------------------------------

    if eta_engine is None:

        raise HTTPException(
            status_code=500,
            detail="ETA Engine is not available."
        )


    # --------------------------------------------------------
    # Validate railway-domain inputs
    # --------------------------------------------------------

    validate_train_state(request)


    # --------------------------------------------------------
    # Convert API request → TrainState
    # --------------------------------------------------------

    state = TrainState(

        train_number=
            request.train_number,

        current_station=
            request.current_station,

        current_route_position=
            request.current_route_position,

        current_arrival_delay=
            request.current_arrival_delay,

        current_departure_delay=
            request.current_departure_delay,

        current_time=
            request.current_time
    )


    # --------------------------------------------------------
    # Run ETA prediction
    # --------------------------------------------------------

    try:

        eta_results = eta_engine.update_state(
            state
        )

    except Exception as e:

        raise HTTPException(

            status_code=400,

            detail=str(e)
        )


    # --------------------------------------------------------
    # Convert result → API response
    # --------------------------------------------------------

    response = build_eta_response(

        state,

        eta_results
    )


    return response


# ============================================================
# PASSENGER ASSISTANCE ENDPOINT
# ============================================================

@app.post("/passenger-assistance")
def passenger_assistance(
    request: PassengerAssistanceRequest
):

    # --------------------------------------------------------
    # Step 1: Check ETA engine
    # --------------------------------------------------------

    if eta_engine is None:

        raise HTTPException(
            status_code=500,
            detail="ETA Engine is not available."
        )


    # --------------------------------------------------------
    # Step 2: Validate passenger information
    # --------------------------------------------------------

    validate_passenger_request(
        request
    )


    # --------------------------------------------------------
    # Step 3: Normalize station codes
    # --------------------------------------------------------

    boarding_station = (
        request.boarding_station
        .strip()
        .upper()
    )

    destination_station = (
        request.destination_station
        .strip()
        .upper()
    )


    # --------------------------------------------------------
    # Step 4: Create ETA request for validation
    # --------------------------------------------------------

    eta_request = ETARequest(

        train_number=
            request.train_number,

        current_station=
            boarding_station,

        current_route_position=
            request.current_route_position,

        current_arrival_delay=
            request.current_arrival_delay,

        current_departure_delay=
            request.current_departure_delay,

        current_time=
            request.current_time
    )


    # --------------------------------------------------------
    # Step 5: Validate train state
    # --------------------------------------------------------

    validate_train_state(
        eta_request
    )


    # --------------------------------------------------------
    # Step 6: Create PassengerRequest
    # --------------------------------------------------------

    passenger = PassengerRequest(

        train_number=
            request.train_number,

        boarding_station=
            boarding_station,

        destination_station=
            destination_station
    )


    # --------------------------------------------------------
    # Step 7: Create TrainState
    # --------------------------------------------------------

    state = TrainState(

        train_number=
            request.train_number,

        current_station=
            boarding_station,

        current_route_position=
            request.current_route_position,

        current_arrival_delay=
            request.current_arrival_delay,

        current_departure_delay=
            request.current_departure_delay,

        current_time=
            request.current_time
    )


    # --------------------------------------------------------
    # Step 8: Run REAL Dynamic ETA Engine
    # --------------------------------------------------------

    try:

        eta_results = eta_engine.update_state(
            state
        )

    except Exception as e:

        raise HTTPException(

            status_code=400,

            detail=str(e)
        )


    # --------------------------------------------------------
    # Step 9: Extract upcoming stations
    # --------------------------------------------------------

    if isinstance(
        eta_results,
        dict
    ):

        upcoming_stations = (
            eta_results.get(
                "upcoming_stations",
                []
            )
        )

    else:

        upcoming_stations = eta_results


    # --------------------------------------------------------
    # Step 10: Normalize ETA results
    # --------------------------------------------------------

    formatted_eta_results = []


    for result in upcoming_stations:

        if not isinstance(
            result,
            dict
        ):
            continue


        # ----------------------------------------------------
        # Find station
        # ----------------------------------------------------

        station = result.get(
            "station"
        )

        if station is None:

            station = result.get(
                "target_station"
            )

        if station is None:

            station = result.get(
                "to_station"
            )

        if station is None:

            station = result.get(
                "station_code"
            )


        if station is None:
            continue


        station = (
            str(station)
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # Find ETA
        # ----------------------------------------------------

        eta = result.get(
            "eta"
        )


        # ----------------------------------------------------
        # Find remaining minutes
        # ----------------------------------------------------

        remaining_minutes = result.get(
            "remaining_minutes"
        )


        if remaining_minutes is None:

            remaining_minutes = result.get(
                "predicted_remaining_minutes"
            )


        # ----------------------------------------------------
        # Add normalized result
        # ----------------------------------------------------

        formatted_eta_results.append(

            {
                "station":
                    station,

                "eta":
                    eta,

                "remaining_minutes":
                    remaining_minutes
            }

        )


    # --------------------------------------------------------
    # Step 11: Create passenger assistance response
    # --------------------------------------------------------

    response = create_assistance_response(

        passenger,

        formatted_eta_results,

        request.current_arrival_delay
    )


    # --------------------------------------------------------
    # Step 12: Return final response
    # --------------------------------------------------------

    return response