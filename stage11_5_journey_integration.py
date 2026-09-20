from passenger_request import PassengerRequest
from stage11_1_journey_validation import validate_passenger_journey
from stage11_2_arrival_timing import get_arrival_timing_status
from stage11_3_arrival_warning import create_arrival_warning
from stage11_4_connection_status import get_connection_status


def create_journey_response(
    passenger,
    eta_result,
    upcoming_stations,
    next_departure_time
):
    """
    Combine passenger journey validation, destination ETA,
    arrival timing, arrival warning, and connection status.
    """

    # ---------------------------------------------------------
    # 1. Validate passenger journey
    # ---------------------------------------------------------
    valid, validation_message = validate_passenger_journey(
        passenger,
        upcoming_stations
    )

    if not valid:
        return {
            "status": "INVALID_JOURNEY",
            "message": validation_message
        }

    # ---------------------------------------------------------
    # 2. Extract ETA information
    # ---------------------------------------------------------
    predicted_eta = eta_result["eta"]
    remaining_minutes = float(
        eta_result["remaining_minutes"]
    )

    # ---------------------------------------------------------
    # 3. Arrival timing status
    # ---------------------------------------------------------
    arrival_status = get_arrival_timing_status(
        remaining_minutes
    )

    # ---------------------------------------------------------
    # 4. Passenger arrival warning
    # ---------------------------------------------------------
    warning = create_arrival_warning(
        passenger.train_number,
        passenger.destination_station,
        remaining_minutes
    )

    # ---------------------------------------------------------
    # 5. Connection status
    # ---------------------------------------------------------
    connection = get_connection_status(
        predicted_eta,
        next_departure_time
    )

    # ---------------------------------------------------------
    # 6. Final passenger journey response
    # ---------------------------------------------------------
    return {
        "status": "OK",
        "train_number": passenger.train_number,
        "boarding_station": passenger.boarding_station,
        "destination_station": passenger.destination_station,
        "predicted_eta": predicted_eta,
        "remaining_minutes": remaining_minutes,
        "arrival_status": arrival_status,
        "arrival_warning": warning["warning"],
        "next_connection_departure": connection[
            "next_departure_time"
        ],
        "transfer_minutes": connection[
            "transfer_minutes"
        ],
        "connection_status": connection[
            "status"
        ]
    }


def run_tests():

    print("=" * 60)
    print("STAGE 11.5 - PASSENGER JOURNEY INTEGRATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # Passenger request
    # ---------------------------------------------------------
    passenger = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="BZL"
    )

    # ---------------------------------------------------------
    # Dynamic ETA result
    # This represents the output already produced by
    # the ETA prediction layer.
    # ---------------------------------------------------------
    eta_result = {
        "eta": "2024-09-26 08:27:55",
        "remaining_minutes": 10.93
    }

    # ---------------------------------------------------------
    # Upcoming stations
    # ---------------------------------------------------------
    upcoming_stations = [
        "BLY",
        "BZL",
        "DKAE",
        "GBRA",
        "JOX"
    ]

    # ---------------------------------------------------------
    # Next connecting train
    # ---------------------------------------------------------
    next_departure_time = "2024-09-26 08:45:00"

    # ---------------------------------------------------------
    # Create complete journey response
    # ---------------------------------------------------------
    response = create_journey_response(
        passenger,
        eta_result,
        upcoming_stations,
        next_departure_time
    )

    print("\nCOMPLETE PASSENGER JOURNEY RESPONSE")
    print("-" * 60)

    for key, value in response.items():
        print(f"{key}: {value}")

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------
    assert response["status"] == "OK"
    assert response["train_number"] == "12303"
    assert response["boarding_station"] == "LLH"
    assert response["destination_station"] == "BZL"

    assert response["predicted_eta"] == "2024-09-26 08:27:55"
    assert response["remaining_minutes"] == 10.93

    assert response["arrival_status"] == "APPROACHING"

    assert "BZL" in response["arrival_warning"]

    assert response["connection_status"] == "AVAILABLE"

    assert response["transfer_minutes"] == 17.08

    print("\nPASS - Complete passenger journey integrated successfully.")

    # ---------------------------------------------------------
    # Invalid journey test
    # ---------------------------------------------------------
    print("\nINVALID JOURNEY TEST")

    invalid_passenger = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="XXXXX"
    )

    invalid_response = create_journey_response(
        invalid_passenger,
        eta_result,
        upcoming_stations,
        next_departure_time
    )

    print(invalid_response)

    assert invalid_response["status"] == "INVALID_JOURNEY"

    print("PASS - Invalid journey safely rejected.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 11.5 TESTS PASSED")
    print("STAGE 11.5: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()