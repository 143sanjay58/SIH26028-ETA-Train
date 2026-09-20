
import os
import pandas as pd


# ============================================================
# DATASET PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "ml_ready_segments_final.csv"
)


# ============================================================
# LOAD DATASET
# ============================================================

_df = pd.read_csv(DATASET_PATH)

_df["train_num_norm"] = (
    _df["train_number"]
    .astype(str)
    .str.strip()
    .str.lstrip("0")
)

_df["train_num_norm"] = _df[
    "train_num_norm"
].replace("", "0")

_df = _df.sort_values(
    ["train_num_norm", "route_order"]
).reset_index(drop=True)


# ============================================================
# GET UPCOMING STATIONS
# ============================================================

def get_upcoming_stations(
    train_number,
    current_route_position
):

    train_number = str(
        train_number
    ).strip().lstrip("0")

    if train_number == "":
        train_number = "0"

    current_route_position = int(
        current_route_position
    )

    train_route = _df[
        _df["train_num_norm"]
        == train_number
    ].copy()

    if train_route.empty:

        raise ValueError(
            f"Train {train_number} "
            "not found in Dataset 1."
        )

    upcoming = train_route[
        train_route["route_order"]
        > current_route_position
    ].copy()

    upcoming = upcoming.sort_values(
        "route_order"
    ).reset_index(drop=True)

    return upcoming


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print(" UPCOMING STATIONS TEST")
    print("======================================")

    train_number = "12303"
    current_position = 2

    upcoming = get_upcoming_stations(
        train_number,
        current_position
    )

    print()
    print("Train:", train_number)
    print(
        "Current route position:",
        current_position
    )

    print(
        "Upcoming station segments:",
        len(upcoming)
    )

    print()

    print(
        upcoming[
            [
                "route_order",
                "from_station",
                "from_station_name",
                "to_station",
                "to_station_name",
                "scheduled_run_minutes"
            ]
        ].head(10).to_string(
            index=False
        )
    )

    print()
    print(
        "Upcoming stations test completed."
    )

