from passenger_request import PassengerRequest
from passenger_assistance_engine import create_assistance_response


def run_test():
    print("=" * 60)
    print("STAGE 10.8 - DYNAMIC PASSENGER ASSISTANCE VALIDATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # Sample dynamic ETA output
    # This represents the output already produced by the
    # Dynamic ETA Engine.
    # ---------------------------------------------------------
    eta_results = [
        {
            "station": "BLY",
            "eta": "2024-09-26 08:25:38",
            "remaining_minutes": 8.65
        },
        {
            "station": "BZL",
            "eta": "2024-09-26 08:27:55",
            "remaining_minutes": 10.93
        },
        {
            "station": "DKAE",
            "eta": "2024-09-26 08:30:55",
            "remaining_minutes": 13.93
        }
    ]

    # ---------------------------------------------------------
    # TEST 1: Valid passenger destination
    # ---------------------------------------------------------
    print("\nTEST 1: Valid destination")

    passenger = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="BZL"
    )

    response = create_assistance_response(
        passenger,
        eta_results,
        current_arrival_delay=17
    )

    print(response)

    assert response["status"] == "OK"
    assert response["train_number"] == "12303"
    assert response["boarding_station"] == "LLH"
    assert response["destination_station"] == "BZL"
    assert response["current_delay_minutes"] == 17
    assert response["delay_status"] == "DELAYED"
    assert response["remaining_minutes"] == 10.93

    print("PASS - Valid destination handled correctly.")

    # ---------------------------------------------------------
    # TEST 2: Unknown destination
    # ---------------------------------------------------------
    print("\nTEST 2: Unknown destination")

    passenger_unknown = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="XXXXX"
    )

    response_unknown = create_assistance_response(
        passenger_unknown,
        eta_results,
        current_arrival_delay=17
    )

    print(response_unknown)

    assert response_unknown["status"] == "DESTINATION_NOT_FOUND"

    print("PASS - Unknown destination handled safely.")

    # ---------------------------------------------------------
    # TEST 3: Dynamic ETA value
    # ---------------------------------------------------------
    print("\nTEST 3: Dynamic ETA verification")

    destination_eta = response["predicted_eta"]
    remaining_time = response["remaining_minutes"]

    print("Predicted ETA:", destination_eta)
    print("Remaining time:", remaining_time)

    assert destination_eta == "2024-09-26 08:27:55"
    assert remaining_time == 10.93

    print("PASS - Passenger assistance uses ETA engine output.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 10.8 VALIDATION TESTS PASSED")
    print("STAGE 10.8: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_test()
    