from eta_refresh_trigger import ETARefreshTrigger


def run_tests():

    print("=" * 60)
    print("STAGE 12.3 - ETA REFRESH TRIGGER")
    print("=" * 60)

    trigger = ETARefreshTrigger()

    # TEST 1
    print("\nTEST 1: Train position changed")

    changes = {
        "station_changed": True,
        "position_changed": True,
        "arrival_delay_changed": False,
        "departure_delay_changed": False,
        "time_changed": True
    }

    result = trigger.should_refresh(changes)

    print("ETA refresh required:", result)

    assert result is True

    print("PASS - Position change triggered ETA refresh.")

    # TEST 2
    print("\nTEST 2: Delay changed")

    changes = {
        "station_changed": False,
        "position_changed": False,
        "arrival_delay_changed": True,
        "departure_delay_changed": True,
        "time_changed": True
    }

    result = trigger.should_refresh(changes)

    print("ETA refresh required:", result)

    assert result is True

    print("PASS - Delay change triggered ETA refresh.")

    # TEST 3
    print("\nTEST 3: Only time changed")

    changes = {
        "station_changed": False,
        "position_changed": False,
        "arrival_delay_changed": False,
        "departure_delay_changed": False,
        "time_changed": True
    }

    result = trigger.should_refresh(changes)

    print("ETA refresh required:", result)

    assert result is False

    print("PASS - Time-only change does not trigger ETA refresh.")

    # TEST 4
    print("\nTEST 4: No state change")

    changes = {
        "station_changed": False,
        "position_changed": False,
        "arrival_delay_changed": False,
        "departure_delay_changed": False,
        "time_changed": False
    }

    result = trigger.should_refresh(changes)

    print("ETA refresh required:", result)

    assert result is False

    print("PASS - No change does not trigger ETA refresh.")

    print("\n" + "=" * 60)
    print("ALL STAGE 12.3 TESTS PASSED")
    print("STAGE 12.3: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()