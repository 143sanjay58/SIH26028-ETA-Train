from passenger_request import PassengerRequest


def validate_passenger_journey(passenger, upcoming_stations):
    """
    Validate whether a passenger journey is logically valid
    for the current train state.
    """

    # Train number
    if not passenger.train_number.strip():
        return False, "Train number is required."

    # Boarding station
    if not passenger.boarding_station.strip():
        return False, "Boarding station is required."

    # Destination station
    if not passenger.destination_station.strip():
        return False, "Destination station is required."

    boarding = passenger.boarding_station.upper()
    destination = passenger.destination_station.upper()

    # Boarding and destination cannot be same
    if boarding == destination:
        return False, "Boarding and destination stations cannot be the same."

    # Normalize upcoming stations
    normalized_upcoming = [
        station.upper() for station in upcoming_stations
    ]

    # Destination must be ahead of current train position
    if destination not in normalized_upcoming:
        return False, "Destination is not available in the upcoming route."

    return True, "Passenger journey is valid."


def run_tests():

    print("=" * 60)
    print("STAGE 11.1 - PASSENGER JOURNEY VALIDATION")
    print("=" * 60)

    upcoming_stations = [
        "BLY",
        "BZL",
        "DKAE",
        "GBRA",
        "JOX"
    ]

    # ---------------------------------------------------------
    # TEST 1: Valid journey
    # ---------------------------------------------------------
    print("\nTEST 1: Valid passenger journey")

    passenger = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="BZL"
    )

    valid, message = validate_passenger_journey(
        passenger,
        upcoming_stations
    )

    print("Result:", valid)
    print("Message:", message)

    assert valid is True

    print("PASS - Valid journey accepted.")

    # ---------------------------------------------------------
    # TEST 2: Same boarding and destination
    # ---------------------------------------------------------
    print("\nTEST 2: Same boarding and destination")

    passenger_same = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="LLH"
    )

    valid, message = validate_passenger_journey(
        passenger_same,
        upcoming_stations
    )

    print("Result:", valid)
    print("Message:", message)

    assert valid is False

    print("PASS - Same station journey rejected.")

    # ---------------------------------------------------------
    # TEST 3: Destination not upcoming
    # ---------------------------------------------------------
    print("\nTEST 3: Destination not in upcoming route")

    passenger_invalid = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="XXXXX"
    )

    valid, message = validate_passenger_journey(
        passenger_invalid,
        upcoming_stations
    )

    print("Result:", valid)
    print("Message:", message)

    assert valid is False

    print("PASS - Invalid destination rejected.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 11.1 TESTS PASSED")
    print("STAGE 11.1: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()