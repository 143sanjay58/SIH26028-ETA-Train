
import os
from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd

from train_state import TrainState
from upcoming_stations import get_upcoming_stations
from eta_predictor import ETAPredictor
from datetime import datetime, timedelta

# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "ml_ready_segments_final.csv"
)


# ============================================================
# DYNAMIC ETA ENGINE
# ============================================================

@dataclass
class DynamicETAEngine:

    def __post_init__(self):

        print("Loading Dynamic ETA Engine...")

        # Load Dataset 1
        self.route_df = pd.read_csv(
            DATASET_PATH
        )

        # Normalize train numbers
        self.route_df[
            "train_num_norm"
        ] = (
            self.route_df[
                "train_number"
            ]
            .astype(str)
            .str.strip()
            .str.lstrip("0")
        )

        self.route_df[
            "train_num_norm"
        ] = self.route_df[
            "train_num_norm"
        ].replace("", "0")

        # Sort route
        self.route_df = (
            self.route_df
            .sort_values(
                [
                    "train_num_norm",
                    "route_order"
                ]
            )
            .reset_index(drop=True)
        )

        # Create ML predictor
        self.predictor = ETAPredictor()

        # Store latest state
        self.last_state = None

        print("Dynamic ETA Engine ready.")


    # ========================================================
    # GET TRAIN ROUTE
    # ========================================================

    def _get_train_route(
        self,
        train_number
    ):

        train_number = (
            str(train_number)
            .strip()
            .lstrip("0")
        )

        if train_number == "":
            train_number = "0"

        route = self.route_df[
            self.route_df[
                "train_num_norm"
            ] == train_number
        ].copy()

        if route.empty:

            raise ValueError(
                f"Train {train_number} "
                "not found in Dataset 1."
            )

        return route.sort_values(
            "route_order"
        ).reset_index(drop=True)


    # ========================================================
    # CALCULATE SCHEDULED REMAINING TIME
    # ========================================================

    def _scheduled_remaining(
        self,
        train_number,
        current_position,
        target_position
    ) -> float:

        route = self._get_train_route(
            train_number
        )

        # ----------------------------------------------------
        # A segment with route_order N connects:
        #
        # station N → station N+1
        #
        # Therefore from current position to target:
        #
        # current_position <= route_order < target_position
        # ----------------------------------------------------

        mask = (

            route["route_order"]
            >= current_position

        ) & (

            route["route_order"]
            < target_position
        )

        selected = route.loc[
            mask,
            "scheduled_run_minutes"
        ]

        if selected.empty:

            return 1.0

        total = selected.sum()

        return max(
            float(total),
            1.0
        )


    # ========================================================
    # VALIDATE TRAIN STATE
    # ========================================================

    @staticmethod
    def _validate_state(
        state: TrainState
    ):

        if not state.train_number:

            raise ValueError(
                "Train number is required."
            )

        if not state.current_station:

            raise ValueError(
                "Current station is required."
            )

        if state.current_route_position < 1:

            raise ValueError(
                "Route position must be >= 1."
            )

        if state.current_arrival_delay < 0:

            raise ValueError(
                "Arrival delay cannot be negative."
            )

        if state.current_departure_delay < 0:

            raise ValueError(
                "Departure delay cannot be negative."
            )


    # ========================================================
    # UPDATE TRAIN STATE
    # ========================================================

    def update_state(
        self,
        state: TrainState
    ) -> List[Dict[str, Any]]:

        print()
        print(
            "Updating train state..."
        )

        self._validate_state(
            state
        )

        # Get all upcoming route segments
        upcoming = get_upcoming_stations(
            state.train_number,
            state.current_route_position
        )

        if upcoming.empty:

            print(
                "No upcoming stations."
            )

            self.last_state = state

            return []


        results = []


        # ----------------------------------------------------
        # ETA consistency tracking
        # ----------------------------------------------------

        previous_eta = None


        # ----------------------------------------------------
        # Predict ETA for every upcoming station
        # ----------------------------------------------------

        for _, row in upcoming.iterrows():

            # route_order N ends at node N+1
            target_position = (
                int(row["route_order"]) + 1
            )

            target_station = (
                row[
                    "to_station_canonical"
                ]
            )

            # Correct scheduled remaining time
            scheduled_remaining = (
                self._scheduled_remaining(
                    train_number=
                        state.train_number,

                    current_position=
                        state.current_route_position,

                    target_position=
                        target_position
                )
            )


            # ------------------------------------------------
            # ML prediction
            # ------------------------------------------------

            prediction = (
                self.predictor.predict(

                    state=state,

                    target_station=
                        target_station,

                    target_route_position=
                        target_position,

                    scheduled_remaining_minutes=
                        scheduled_remaining
                )
            )


            # ------------------------------------------------
            # Raw ML prediction
            # ------------------------------------------------

            raw_eta = prediction["eta"]

            raw_remaining = float(
                prediction[
                    "predicted_remaining_minutes"
                ]
            )


            # ------------------------------------------------
            # ETA consistency correction
            # ------------------------------------------------
            #
            # A downstream station must not have an ETA
            # earlier than the previous station.
            #

            corrected_eta = raw_eta

            if previous_eta is not None:

                # Minimum logical travel time to the next station
                minimum_gap_minutes = float(
                    row["scheduled_run_minutes"]
                )

                minimum_allowed_eta = (
                    previous_eta
                    + timedelta(
                        minutes=minimum_gap_minutes
                    )
                )

                if corrected_eta < minimum_allowed_eta:

                    corrected_eta = minimum_allowed_eta


            # Recalculate remaining time from corrected ETA
            corrected_remaining = (
                corrected_eta - state.current_time
            ).total_seconds() / 60.0


            results.append({

                "train_number":
                    state.train_number,

                "current_station":
                    state.current_station,

                "current_route_position":
                    state.current_route_position,

                "target_station":
                    target_station,

                "target_station_name":
                    row[
                        "to_station_name"
                    ],

                "target_route_position":
                    target_position,

                "scheduled_remaining_minutes":
                    scheduled_remaining,

                # Final serving prediction
                "predicted_remaining_minutes":
                    round(
                        corrected_remaining,
                        2
                    ),

                "predicted_future_arrival_delay":
                    prediction[
                        "predicted_future_arrival_delay"
                    ],

                # Final consistent ETA
                "eta":
                    corrected_eta,

                # Keep raw ML output for debugging
                "raw_predicted_remaining_minutes":
                    round(
                        raw_remaining,
                        2
                    ),

                "raw_eta":
                    raw_eta
            })


            # Update previous ETA
            previous_eta = corrected_eta


        # Save latest state
        self.last_state = state

        return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )
    print(
        " STAGE 8.6 - DYNAMIC ETA ENGINE"
    )
    print(
        "=========================================="
    )


    # ========================================================
    # CREATE ENGINE
    # ========================================================

    engine = DynamicETAEngine()


    # ========================================================
    # UPDATE 1
    # ========================================================

    state_1 = TrainState(

        train_number="12303",

        current_station="LLH",

        current_route_position=2,

        current_arrival_delay=15,

        current_departure_delay=17,

        current_time=pd.Timestamp(
            "2024-09-26 08:13"
        ).to_pydatetime()
    )


    result_1 = engine.update_state(
        state_1
    )


    print()
    print(
        "========== UPDATE 1 =========="
    )

    print(
        "Current station:",
        state_1.current_station
    )

    print(
        "Route position:",
        state_1.current_route_position
    )

    print(
        "Arrival delay:",
        state_1.current_arrival_delay,
        "minutes"
    )

    print(
        "Departure delay:",
        state_1.current_departure_delay,
        "minutes"
    )

    print(
        "Upcoming stations:",
        len(result_1)
    )

    print()

    for item in result_1[:5]:

        print(
            item["target_station"],
            "|",
            item[
                "target_station_name"
            ],
            "| Scheduled:",
            round(
                item[
                    "scheduled_remaining_minutes"
                ],
                2
            ),
            "min",
            "| Predicted:",
            round(
                item[
                    "predicted_remaining_minutes"
                ],
                2
            ),
            "min",
            "| Future delay:",
            round(
                item[
                    "predicted_future_arrival_delay"
                ],
                2
            ),
            "min",
            "| ETA:",
            item["eta"]
        )


    # ========================================================
    # UPDATE 2
    # ========================================================

    state_2 = TrainState(

        train_number="12303",

        current_station="BEQ",

        current_route_position=3,

        current_arrival_delay=18,

        current_departure_delay=20,

        current_time=pd.Timestamp(
            "2024-09-26 08:20"
        ).to_pydatetime()
    )


    result_2 = engine.update_state(
        state_2
    )


    print()
    print(
        "========== UPDATE 2 =========="
    )

    print(
        "Current station:",
        state_2.current_station
    )

    print(
        "Route position:",
        state_2.current_route_position
    )

    print(
        "Arrival delay:",
        state_2.current_arrival_delay,
        "minutes"
    )

    print(
        "Departure delay:",
        state_2.current_departure_delay,
        "minutes"
    )

    print(
        "Upcoming stations:",
        len(result_2)
    )

    print()

    for item in result_2[:5]:

        print(
            item["target_station"],
            "|",
            item[
                "target_station_name"
            ],
            "| Scheduled:",
            round(
                item[
                    "scheduled_remaining_minutes"
                ],
                2
            ),
            "min",
            "| Predicted:",
            round(
                item[
                    "predicted_remaining_minutes"
                ],
                2
            ),
            "min",
            "| Future delay:",
            round(
                item[
                    "predicted_future_arrival_delay"
                ],
                2
            ),
            "min",
            "| ETA:",
            item["eta"]
        )


    # ========================================================
    # DYNAMIC CHECK
    # ========================================================

    targets_1 = {
        item["target_station"]
        for item in result_1
    }

    targets_2 = {
        item["target_station"]
        for item in result_2
    }


    print()
    print("Stage 8.6 test completed." )
        
