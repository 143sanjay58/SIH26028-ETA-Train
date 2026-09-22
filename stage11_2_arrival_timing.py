def get_arrival_timing_status(remaining_minutes):
    """
    Determine the passenger's destination arrival timing
    from the predicted remaining travel time.
    """

    remaining_minutes = float(remaining_minutes)

    if remaining_minutes <= 0:
        return "ARRIVED"

    elif remaining_minutes <= 10:
        return "NEAR"

    elif remaining_minutes <= 30:
        return "APPROACHING"

    else:
        return "IN_PROGRESS"


def run_tests():

    print("=" * 60)
    print("STAGE 11.2 - DESTINATION ARRIVAL TIMING")
    print("=" * 60)

    # ---------------------------------------------------------
    # TEST 1
    # ---------------------------------------------------------
    print("\nTEST 1: Long remaining time")

    status = get_arrival_timing_status(45)

    print("Remaining:", 45, "minutes")
    print("Status:", status)

    assert status == "IN_PROGRESS"

    print("PASS - Long journey correctly identified.")

    # ---------------------------------------------------------
    # TEST 2
    # ---------------------------------------------------------
    print("\nTEST 2: Approaching destination")

    status = get_arrival_timing_status(20)

    print("Remaining:", 20, "minutes")
    print("Status:", status)

    assert status == "APPROACHING"

    print("PASS - Approaching destination correctly identified.")

    # ---------------------------------------------------------
    # TEST 3
    # ---------------------------------------------------------
    print("\nTEST 3: Near destination")

    status = get_arrival_timing_status(8.5)

    print("Remaining:", 8.5, "minutes")
    print("Status:", status)

    assert status == "NEAR"

    print("PASS - Near destination correctly identified.")

    # ---------------------------------------------------------
    # TEST 4
    # ---------------------------------------------------------
    print("\nTEST 4: Destination reached")

    status = get_arrival_timing_status(0)

    print("Remaining:", 0, "minutes")
    print("Status:", status)

    assert status == "ARRIVED"

    print("PASS - Arrival correctly identified.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 11.2 TESTS PASSED")
    print("STAGE 11.2: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()