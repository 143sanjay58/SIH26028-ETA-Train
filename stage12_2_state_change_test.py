from datetime import datetime

from train_state import TrainState
from state_change_detector import StateChangeDetector


def run_tests():

    print("=" * 60)
    print("STAGE 12.2 - STATE CHANGE DETECTION")
    print("=" * 60)

    detector = StateChangeDetector()

    # --------------------------------------------------
    # TEST 1: Station and position changed
    # --------------------------------------------------

    print("\nTEST 1: Station and position change")

    old_state = TrainState(
        train_number="12303",
        current_station="LLH",
        current_route_position=2,
        current_arrival_delay=15,
        current_departure_delay=17,
        current_time=datetime(2024, 9, 26, 8, 10)
    )

    new_state = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=16,
        current_departure_delay=18,
        current_time=datetime(2024, 9, 26, 8, 14)
    )

    changes = detector.detect_changes(old_state, new_state)

    print("Station changed:", changes["station_changed"])
    print("Position changed:", changes["position_changed"])
    print("Arrival delay changed:", changes["arrival_delay_changed"])
    print("Departure delay changed:", changes["departure_delay_changed"])
    print("Time changed:", changes["time_changed"])
    print("Any change:", changes["any_change"])

    assert changes["station_changed"] is True
    assert changes["position_changed"] is True
    assert changes["arrival_delay_changed"] is True
    assert changes["departure_delay_changed"] is True
    assert changes["time_changed"] is True
    assert changes["any_change"] is True

    print("PASS - State changes detected correctly.")

    # --------------------------------------------------
    # TEST 2: Only delay changed
    # --------------------------------------------------

    print("\nTEST 2: Delay-only change")

    old_state = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=16,
        current_departure_delay=18,
        current_time=datetime(2024, 9, 26, 8, 14)
    )

    new_state = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=20,
        current_departure_delay=22,
        current_time=datetime(2024, 9, 26, 8, 16)
    )

    changes = detector.detect_changes(old_state, new_state)

    print("Station changed:", changes["station_changed"])
    print("Position changed:", changes["position_changed"])
    print("Arrival delay changed:", changes["arrival_delay_changed"])
    print("Departure delay changed:", changes["departure_delay_changed"])
    print("Time changed:", changes["time_changed"])
    print("Any change:", changes["any_change"])

    assert changes["station_changed"] is False
    assert changes["position_changed"] is False
    assert changes["arrival_delay_changed"] is True
    assert changes["departure_delay_changed"] is True
    assert changes["time_changed"] is True
    assert changes["any_change"] is True

    print("PASS - Delay change detected correctly.")

    # --------------------------------------------------
    # TEST 3: No change
    # --------------------------------------------------

    print("\nTEST 3: No state change")

    same_state_1 = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=20,
        current_departure_delay=22,
        current_time=datetime(2024, 9, 26, 8, 16)
    )

    same_state_2 = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=20,
        current_departure_delay=22,
        current_time=datetime(2024, 9, 26, 8, 16)
    )

    changes = detector.detect_changes(
        same_state_1,
        same_state_2
    )

    print("Station changed:", changes["station_changed"])
    print("Position changed:", changes["position_changed"])
    print("Arrival delay changed:", changes["arrival_delay_changed"])
    print("Departure delay changed:", changes["departure_delay_changed"])
    print("Time changed:", changes["time_changed"])
    print("Any change:", changes["any_change"])

    assert changes["station_changed"] is False
    assert changes["position_changed"] is False
    assert changes["arrival_delay_changed"] is False
    assert changes["departure_delay_changed"] is False
    assert changes["time_changed"] is False
    assert changes["any_change"] is False

    print("PASS - No-change state detected correctly.")

    # --------------------------------------------------
    # TEST 4: Train number change rejection
    # --------------------------------------------------

    print("\nTEST 4: Train number change")

    other_train = TrainState(
        train_number="99999",
        current_station="BLY",
        current_route_position=4,
        current_arrival_delay=10,
        current_departure_delay=12,
        current_time=datetime(2024, 9, 26, 8, 20)
    )

    try:
        detector.detect_changes(
            same_state_1,
            other_train
        )

        assert False, "Train number change was not rejected."

    except ValueError as error:
        print("Rejected:", error)
        print("PASS - Train number change rejected.")

    print("\n" + "=" * 60)
    print("ALL STAGE 12.2 TESTS PASSED")
    print("STAGE 12.2: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()