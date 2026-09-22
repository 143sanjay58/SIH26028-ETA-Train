def create_arrival_warning(
    train_number,
    destination_station,
    remaining_minutes
):
    """
    Create a passenger-friendly arrival message
    based on predicted remaining travel time.
    """

    remaining_minutes = float(remaining_minutes)

    if remaining_minutes <= 0:

        return {
            "status": "ARRIVED",
            "train_number": train_number,
            "destination_station": destination_station,
            "remaining_minutes": remaining_minutes,
            "warning": "You have arrived at your destination."
        }

    elif remaining_minutes <= 10:

        return {
            "status": "NEAR",
            "train_number": train_number,
            "destination_station": destination_station,
            "remaining_minutes": remaining_minutes,
            "warning": (
                f"Your destination {destination_station} "
                f"is approaching. Please prepare to get down."
            )
        }

    elif remaining_minutes <= 30:

        return {
            "status": "APPROACHING",
            "train_number": train_number,
            "destination_station": destination_station,
            "remaining_minutes": remaining_minutes,
            "warning": (
                f"Your destination {destination_station} "
                f"is approximately {remaining_minutes:.2f} "
                f"minutes away."
            )
        }

    else:

        return {
            "status": "IN_PROGRESS",
            "train_number": train_number,
            "destination_station": destination_station,
            "remaining_minutes": remaining_minutes,
            "warning": (
                f"Your journey is in progress. "
                f"Estimated time to {destination_station}: "
                f"{remaining_minutes:.2f} minutes."
            )
        }


def run_tests():

    print("=" * 60)
    print("STAGE 11.3 - PASSENGER ARRIVAL WARNING")
    print("=" * 60)

    # ---------------------------------------------------------
    # TEST 1: Journey in progress
    # ---------------------------------------------------------
    print("\nTEST 1: Journey in progress")

    response = create_arrival_warning(
        "12303",
        "BZL",
        45
    )

    print(response)

    assert response["status"] == "IN_PROGRESS"
    assert response["destination_station"] == "BZL"

    print("PASS - Journey progress message generated.")

    # ---------------------------------------------------------
    # TEST 2: Destination approaching
    # ---------------------------------------------------------
    print("\nTEST 2: Destination approaching")

    response = create_arrival_warning(
        "12303",
        "BZL",
        20
    )

    print(response)

    assert response["status"] == "APPROACHING"
    assert response["remaining_minutes"] == 20

    print("PASS - Approaching warning generated.")

    # ---------------------------------------------------------
    # TEST 3: Destination near
    # ---------------------------------------------------------
    print("\nTEST 3: Destination near")

    response = create_arrival_warning(
        "12303",
        "BZL",
        8.5
    )

    print(response)

    assert response["status"] == "NEAR"
    assert "prepare to get down" in response["warning"]

    print("PASS - Near-destination warning generated.")

    # ---------------------------------------------------------
    # TEST 4: Destination reached
    # ---------------------------------------------------------
    print("\nTEST 4: Destination reached")

    response = create_arrival_warning(
        "12303",
        "BZL",
        0
    )

    print(response)

    assert response["status"] == "ARRIVED"
    assert "arrived" in response["warning"].lower()

    print("PASS - Arrival message generated.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 11.3 TESTS PASSED")
    print("STAGE 11.3: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()