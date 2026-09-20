import os
import joblib
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "ml_ready_segments_final.csv"
)

SCHEMA_PATH = os.path.join(
    BASE_DIR,
    "feature_encoders_and_schema.joblib"
)


# ============================================================
# FEATURE BUILDER
# ============================================================

class FeatureBuilder:

    def __init__(self):

        print("Loading Dataset 1...")

        self.df = pd.read_csv(DATASET_PATH)

        print(
            "Dataset loaded:",
            len(self.df),
            "rows"
        )

        print("Loading ML schema...")

        self.schema = joblib.load(SCHEMA_PATH)

        print("ML schema loaded.")

        # ----------------------------------------------------
        # Get encoders
        # ----------------------------------------------------

        self.encoders = self.schema.get(
            "encoders",
            {}
        )

        # ----------------------------------------------------
        # Create train number lookup
        # ----------------------------------------------------

        self.df["train_num_norm"] = (
            self.df["train_number"]
            .astype(str)
            .str.strip()
            .str.lstrip("0")
        )

        self.df.loc[
            self.df["train_num_norm"] == "",
            "train_num_norm"
        ] = "0"

        # ----------------------------------------------------
        # Sort route
        # ----------------------------------------------------

        self.df = self.df.sort_values(
            [
                "train_num_norm",
                "route_order"
            ]
        ).reset_index(drop=True)

        print("Feature Builder ready.")

    # ========================================================
    # ENCODING
    # ========================================================

    def _encode_value(self, column, value):

        encoder = self.encoders.get(column)

        if encoder is None:
            return 0

        # Dictionary encoder
        if isinstance(encoder, dict):

            return encoder.get(
                str(value),
                0
            )

        # sklearn-style encoder
        try:

            return int(
                encoder.transform(
                    [str(value)]
                )[0]
            )

        except Exception:

            return 0

    # ========================================================
    # FIND D1 TRAIN ROUTE
    # ========================================================

    def get_train_route(self, train_number):

        train_number = str(
            train_number
        ).strip().lstrip("0")

        if train_number == "":
            train_number = "0"

        route = self.df[
            self.df["train_num_norm"]
            == train_number
        ].copy()

        return route.sort_values(
            "route_order"
        )

    # ========================================================
    # BUILD FEATURES
    # ========================================================

    def build(
        self,
        state,
        target_station,
        target_route_position,
        scheduled_remaining_minutes,
        total_route_positions=None
    ):

        train_number = str(
            state.train_number
        ).strip().lstrip("0")

        if train_number == "":
            train_number = "0"

        current_station = str(
            state.current_station
        ).strip()

        target_station = str(
            target_station
        ).strip()

        current_position = int(
            state.current_route_position
        )

        target_position = int(
            target_route_position
        )

        # ----------------------------------------------------
        # Route
        # ----------------------------------------------------

        route = self.get_train_route(
            train_number
        )

        # Use target position from model input
        # when D1 route has a different representation.
        if total_route_positions is None:
            if not route.empty:
                total_route_positions = int(route["route_order"].max()) + 1
            else:
                total_route_positions = max(target_position, current_position)

        # ----------------------------------------------------
        # Stations ahead
        # ----------------------------------------------------

        stations_ahead = max(
            target_position - current_position,
            0
        )

        remaining_route_positions = max(
            total_route_positions - current_position,
            0
        )

        # ----------------------------------------------------
        # Distance in route positions
        # ----------------------------------------------------

        target_distance_positions = max(
            target_position - current_position,
            0
        )

        # ----------------------------------------------------
        # Delay change
        # ----------------------------------------------------

        current_delay_change = (
            float(state.current_departure_delay)
            -
            float(state.current_arrival_delay)
        )

        # ----------------------------------------------------
        # Route progress
        # ----------------------------------------------------

        if total_route_positions > 0:

            route_progress_pct = (
                current_position
                /
                total_route_positions
            )

        else:

            route_progress_pct = 0.0

        route_progress_pct = max(
            0.0,
            min(
                1.0,
                route_progress_pct
            )
        )

        # ----------------------------------------------------
        # D1 scheduled remaining
        # ----------------------------------------------------

        d1_scheduled_remaining_minutes = 0.0

        has_d1_schedule_match = 0

        if not route.empty:

            current_match = route[
                (
                    route["route_order"]
                    == current_position
                )
            ]

            target_match = route[
                (
                    route["route_order"]
                    == target_position - 1
                )
            ]

            if (
                not current_match.empty
                and
                not target_match.empty
            ):

                between = route[
                    (
                        route["route_order"]
                        >= current_position
                    )
                    &
                    (
                        route["route_order"]
                        < target_position
                    )
                ]

                d1_scheduled_remaining_minutes = (
                    between[
                        "scheduled_run_minutes"
                    ]
                    .fillna(0)
                    .sum()
                )

                has_d1_schedule_match = 1

        # ----------------------------------------------------
        # Current time features
        # ----------------------------------------------------

        current_time = state.current_time

        current_hour = current_time.hour
        current_minute = current_time.minute

        day_of_week = current_time.weekday()

        is_weekend = int(
            day_of_week >= 5
        )

        is_night = int(
            current_hour < 6
            or
            current_hour >= 22
        )

        is_peak_hour = int(
            current_hour in [
                7,
                8,
                9,
                17,
                18,
                19
            ]
        )

        # ----------------------------------------------------
        # Encode categorical features
        # ----------------------------------------------------

        train_code = self._encode_value(
            "train_num_norm",
            train_number
        )

        current_station_code = self._encode_value(
            "current_station",
            current_station
        )

        target_station_code = self._encode_value(
            "target_station",
            target_station
        )

        # ----------------------------------------------------
        # FINAL 21 FEATURES
        # ----------------------------------------------------

        features = {

            "train_num_norm_code":
                train_code,

            "current_station_code":
                current_station_code,

            "target_station_code":
                target_station_code,

            "current_route_position":
                current_position,

            "target_route_position":
                target_position,

            "stations_ahead":
                stations_ahead,

            "scheduled_remaining_minutes":
                float(
                    scheduled_remaining_minutes
                ),

            "current_arrival_delay":
                float(
                    state.current_arrival_delay
                ),

            "current_departure_delay":
                float(
                    state.current_departure_delay
                ),

            "current_delay_change":
                current_delay_change,

            "route_progress_pct":
                route_progress_pct,

            "remaining_route_positions":
                remaining_route_positions,

            "target_distance_positions":
                target_distance_positions,

            "d1_scheduled_remaining_minutes":
                float(
                    d1_scheduled_remaining_minutes
                ),

            "has_d1_schedule_match":
                has_d1_schedule_match,

            "current_hour":
                current_hour,

            "current_minute":
                current_minute,

            "day_of_week":
                day_of_week,

            "is_weekend":
                is_weekend,

            "is_night":
                is_night,

            "is_peak_hour":
                is_peak_hour
        }

        # ----------------------------------------------------
        # DataFrame in EXACT model order
        # ----------------------------------------------------

        feature_order = [

            "train_num_norm_code",
            "current_station_code",
            "target_station_code",
            "current_route_position",
            "target_route_position",
            "stations_ahead",
            "scheduled_remaining_minutes",
            "current_arrival_delay",
            "current_departure_delay",
            "current_delay_change",
            "route_progress_pct",
            "remaining_route_positions",
            "target_distance_positions",
            "d1_scheduled_remaining_minutes",
            "has_d1_schedule_match",
            "current_hour",
            "current_minute",
            "day_of_week",
            "is_weekend",
            "is_night",
            "is_peak_hour"
        ]

        return pd.DataFrame(
            [[features[column]
              for column in feature_order]],
            columns=feature_order
        )


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    from datetime import datetime
    from train_state import TrainState

    print(
        "\n======================================"
    )
    print(
        " FEATURE BUILDER TEST"
    )
    print(
        "======================================"
    )

    builder = FeatureBuilder()

    state = TrainState(
        train_number="12303",
        current_station="LLH",
        current_route_position=2,
        current_arrival_delay=15,
        current_departure_delay=17,
        current_time=datetime(
            2024,
            9,
            26,
            8,
            13
        )
    )

    features = builder.build(
        state=state,
        target_station="BLY",
        target_route_position=4,
        scheduled_remaining_minutes=3
    )

    print("\nFeature count:")
    print(len(features.columns))

    print("\nFeatures:")
    print(features.to_string(index=False))

    print(
        "\nFeature Builder test completed."
    )