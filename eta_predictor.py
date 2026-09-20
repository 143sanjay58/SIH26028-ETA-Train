
import os
from datetime import timedelta

import joblib

from feature_builder import FeatureBuilder
from train_state import TrainState


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# ML MODEL PATHS
# ============================================================

REMAINING_MODEL_PATH = os.path.join(
    BASE_DIR,
    "eta_remaining_time_lgbm.joblib"
)

DELAY_MODEL_PATH = os.path.join(
    BASE_DIR,
    "future_arrival_delay_lgbm.joblib"
)


# ============================================================
# ETA PREDICTOR
# ============================================================

class ETAPredictor:

    def __init__(self):

        print("Loading ETA ML models...")

        self.feature_builder = FeatureBuilder()

        self.remaining_model = joblib.load(
            REMAINING_MODEL_PATH
        )

        self.delay_model = joblib.load(
            DELAY_MODEL_PATH
        )

        print("ETA ML models loaded.")


    # ========================================================
    # PREDICT ETA
    # ========================================================

    def predict(
        self,
        state: TrainState,
        target_station: str,
        target_route_position: int,
        scheduled_remaining_minutes: float
    ):

        # ----------------------------------------------------
        # Build the 21 ML features
        # ----------------------------------------------------

        features = self.feature_builder.build(

            state=state,

            target_station=target_station,

            target_route_position=
                target_route_position,

            scheduled_remaining_minutes=
                scheduled_remaining_minutes
        )


        # ----------------------------------------------------
        # Predict remaining travel time
        # ----------------------------------------------------

        predicted_remaining = (
            self.remaining_model.predict(
                features
            )[0]
        )

        predicted_remaining = max(
            float(predicted_remaining),
            1.0
        )


        # ----------------------------------------------------
        # Predict future arrival delay
        # ----------------------------------------------------

        predicted_delay = (
            self.delay_model.predict(
                features
            )[0]
        )

        predicted_delay = max(
            float(predicted_delay),
            0.0
        )


        # ----------------------------------------------------
        # Calculate ETA
        # ----------------------------------------------------

        eta_time = (
            state.current_time
            +
            timedelta(
                minutes=predicted_remaining
            )
        )


        return {

            "predicted_remaining_minutes":
                predicted_remaining,

            "predicted_future_arrival_delay":
                predicted_delay,

            "eta":
                eta_time
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print(" ETA PREDICTOR TEST")
    print("======================================")


    state = TrainState(

        train_number="12303",

        current_station="LLH",

        current_route_position=2,

        current_arrival_delay=15,

        current_departure_delay=17,

        current_time=None
    )


    # Use a real test time
    from datetime import datetime

    state.current_time = datetime(
        2024,
        9,
        26,
        8,
        13
    )


    predictor = ETAPredictor()


    result = predictor.predict(

        state=state,

        target_station="BLY",

        target_route_position=4,

        scheduled_remaining_minutes=3
    )


    print()

    print(
        "Predicted remaining time:",
        round(
            result[
                "predicted_remaining_minutes"
            ],
            2
        ),
        "minutes"
    )

    print(
        "Predicted future delay:",
        round(
            result[
                "predicted_future_arrival_delay"
            ],
            2
        ),
        "minutes"
    )

    print(
        "Predicted ETA:",
        result["eta"]
    )

    print()

    print(
        "ETA Predictor test completed."
    )

