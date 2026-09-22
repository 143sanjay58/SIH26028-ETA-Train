from datetime import datetime


def get_connection_status(arrival_time, next_departure_time):
    """
    Determine whether a passenger has enough time
    to catch the next connecting train.
    """

    if not isinstance(arrival_time, datetime):
        arrival_time = datetime.fromisoformat(str(arrival_time))

    if not isinstance(next_departure_time, datetime):
        next_departure_time = datetime.fromisoformat(
            str(next_departure_time)
        )

    transfer_minutes = (
        next_departure_time - arrival_time
    ).total_seconds() / 60

    if transfer_minutes < 0:
        status = "MISSED"

    elif transfer_minutes <= 5:
        status = "VERY_TIGHT"

    elif transfer_minutes <= 15:
        status = "TIGHT"

    else:
        status = "AVAILABLE"

    return {
        "arrival_time": arrival_time,
        "next_departure_time": next_departure_time,
        "transfer_minutes": round(transfer_minutes, 2),
        "status": status
    }


def run_tests():

    print("=" * 60)
    print("STAGE 11.4 - CONNECTION STATUS")
    print("=" * 60)

    # ---------------------------------------------------------
    # TEST 1: Connection available
    # ---------------------------------------------------------
    print("\nTEST 1: Comfortable connection")

    result = get_connection_status(
        "2024-09-26 08:27:55",
        "2024-09-26 08:45:00"
    )

    print(result)

    assert result["status"] == "AVAILABLE"
    assert result["transfer_minutes"] > 15

    print("PASS - Connection correctly identified as available.")

    # ---------------------------------------------------------
    # TEST 2: Tight connection
    # ---------------------------------------------------------
    print("\nTEST 2: Tight connection")

    result = get_connection_status(
        "2024-09-26 08:27:55",
        "2024-09-26 08:38:00"
    )

    print(result)

    assert result["status"] == "TIGHT"
    assert 5 < result["transfer_minutes"] <= 15

    print("PASS - Tight connection correctly identified.")

    # ---------------------------------------------------------
    # TEST 3: Very tight connection
    # ---------------------------------------------------------
    print("\nTEST 3: Very tight connection")

    result = get_connection_status(
        "2024-09-26 08:27:55",
        "2024-09-26 08:31:00"
    )

    print(result)

    assert result["status"] == "VERY_TIGHT"
    assert 0 <= result["transfer_minutes"] <= 5

    print("PASS - Very tight connection correctly identified.")

    # ---------------------------------------------------------
    # TEST 4: Connection missed
    # ---------------------------------------------------------
    print("\nTEST 4: Missed connection")

    result = get_connection_status(
        "2024-09-26 08:27:55",
        "2024-09-26 08:20:00"
    )

    print(result)

    assert result["status"] == "MISSED"
    assert result["transfer_minutes"] < 0

    print("PASS - Missed connection correctly identified.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 11.4 TESTS PASSED")
    print("STAGE 11.4: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()