
from typing import List, Dict, Any


def build_eta_response(
    state,
    eta_results: List[Dict[str, Any]]
):
    """
    Convert Dynamic ETA Engine results
    into a clean API response.
    """

    # --------------------------------------------------------
    # Current delay
    # --------------------------------------------------------

    current_delay = max(
        float(state.current_departure_delay),
        float(state.current_arrival_delay)
    )


    # --------------------------------------------------------
    # Upcoming station responses
    # --------------------------------------------------------

    upcoming_stations = []

    for item in eta_results:

        upcoming_stations.append({

            "station_code":
                item["target_station"],

            "station_name":
                item["target_station_name"],

            "route_position":
                int(
                    item["target_route_position"]
                ),

            "scheduled_remaining_minutes":
                round(
                    float(
                        item[
                            "scheduled_remaining_minutes"
                        ]
                    ),
                    2
                ),

            "predicted_remaining_minutes":
                round(
                    float(
                        item[
                            "predicted_remaining_minutes"
                        ]
                    ),
                    2
                ),

            "predicted_arrival_delay_minutes":
                round(
                    float(
                        item[
                            "predicted_future_arrival_delay"
                        ]
                    ),
                    2
                ),

            "predicted_eta":
                item["eta"].isoformat()
        })


    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    response = {

        "status": "success",

        "train": {

            "train_number":
                state.train_number,

            "current_station":
                state.current_station,

            "current_route_position":
                int(
                    state.current_route_position
                ),

            "current_arrival_delay_minutes":
                round(
                    float(
                        state.current_arrival_delay
                    ),
                    2
                ),

            "current_departure_delay_minutes":
                round(
                    float(
                        state.current_departure_delay
                    ),
                    2
                ),

            "current_delay_minutes":
                round(
                    current_delay,
                    2
                ),

            "current_time":
                state.current_time.isoformat()
        },

        "prediction": {

            "upcoming_station_count":
                len(upcoming_stations),

            "upcoming_stations":
                upcoming_stations
        }
    }


    return response


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from datetime import datetime
    from train_state import TrainState


    print()
    print(
        "=========================================="
    )
    print(
        " STAGE 8.7.1 - ETA RESPONSE TEST"
    )
    print(
        "=========================================="
    )


    state = TrainState(

        train_number="12303",

        current_station="BEQ",

        current_route_position=3,

        current_arrival_delay=18,

        current_departure_delay=20,

        current_time=datetime(
            2024,
            9,
            26,
            8,
            20
        )
    )


    # Simulated engine result
    test_results = [

        {

            "target_station":
                "BZL",

            "target_station_name":
                "BELANAGAR",

            "target_route_position":
                4,

            "scheduled_remaining_minutes":
                3.0,

            "predicted_remaining_minutes":
                6.67,

            "predicted_future_arrival_delay":
                25.05,

            "eta":
                datetime(
                    2024,
                    9,
                    26,
                    8,
                    26,
                    40
                )
        },

        {

            "target_station":
                "DKAE",

            "target_station_name":
                "DANKUNI",

            "target_route_position":
                5,

            "scheduled_remaining_minutes":
                6.0,

            "predicted_remaining_minutes":
                9.41,

            "predicted_future_arrival_delay":
                25.45,

            "eta":
                datetime(
                    2024,
                    9,
                    26,
                    8,
                    29,
                    24
                )
        }
    ]


    response = build_eta_response(
        state,
        test_results
    )


    # --------------------------------------------------------
    # Display response
    # --------------------------------------------------------

    import json

    print()

    print(
        json.dumps(
            response,
            indent=4
        )
    )


    print()
    print(
        "ETA response test completed."
    )

