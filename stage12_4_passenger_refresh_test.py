from passenger_request import PassengerRequest
from passenger_information_refresh import PassengerInformationRefresh


def run_tests():

    print("=" * 60)
    print("STAGE 12.4 - PASSENGER INFORMATION REFRESH")
    print("=" * 60)

    refresher = PassengerInformationRefresh()

    passenger = PassengerRequest(
        train_number="12303",
        boarding_station="LLH",
        destination_station="BZL"
    )

    updated_journey = {
        "predicted_eta": "2024-09-26T08:27:55",
        "remaining_minutes": 10.93,
        "arrival_status": "APPROACHING",
        "connection_status": "AVAILABLE"
    }

    print("\nTEST 1: Refresh passenger information")

    result = refresher.refresh(
        passenger,
        updated_journey
    )

    print("Train:", result["train_number"])
    print("Boarding:", result["boarding_station"])
    print("Destination:", result["destination_station"])
    print("Predicted ETA:", result["predicted_eta"])
    print("Remaining:", result["remaining_minutes"])
    print("Arrival status:", result["arrival_status"])
    print("Connection:", result["connection_status"])

    assert result["train_number"] == "12303"
    assert result["boarding_station"] == "LLH"
    assert result["destination_station"] == "BZL"
    assert result["predicted_eta"] == "2024-09-26T08:27:55"
    assert result["remaining_minutes"] == 10.93
    assert result["arrival_status"] == "APPROACHING"
    assert result["connection_status"] == "AVAILABLE"

    print("PASS - Passenger information refreshed.")

    print("\nTEST 2: Verify updated ETA")

    updated_journey["predicted_eta"] = "2024-09-26T08:31:20"

    result = refresher.refresh(
        passenger,
        updated_journey
    )

    print("New predicted ETA:", result["predicted_eta"])

    assert result["predicted_eta"] == "2024-09-26T08:31:20"

    print("PASS - Passenger ETA updated successfully.")

    print("\n" + "=" * 60)
    print("ALL STAGE 12.4 TESTS PASSED")
    print("STAGE 12.4: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()