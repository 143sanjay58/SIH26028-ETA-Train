from datetime import datetime

from train_state import TrainState
from train_state_manager import TrainStateManager


def run_tests():

    print("=" * 60)
    print("STAGE 12.1 - TRAIN STATE UPDATE MANAGER")
    print("=" * 60)

    manager = TrainStateManager()

    # ---------------------------------------------------------
    # TEST 1: First state
    # ---------------------------------------------------------
    print("\nTEST 1: Initial train state")

    state1 = TrainState(
        train_number="12303",
        current_station="LLH",
        current_route_position=2,
        current_arrival_delay=15,
        current_departure_delay=17,
        current_time=datetime(2024, 9, 26, 8, 10)
    )

    result = manager.update_state(state1)

    print("Train:", result.train_number)
    print("Station:", result.current_station)
    print("Position:", result.current_route_position)
    print("Arrival delay:", result.current_arrival_delay)

    assert result.train_number == "12303"
    assert result.current_station == "LLH"
    assert result.current_route_position == 2

    print("PASS - Initial state stored.")

    # ---------------------------------------------------------
    # TEST 2: Forward state update
    # ---------------------------------------------------------
    print("\nTEST 2: Forward train movement")

    state2 = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=16,
        current_departure_delay=18,
        current_time=datetime(2024, 9, 26, 8, 14)
    )

    result = manager.update_state(state2)

    print("Train:", result.train_number)
    print("Station:", result.current_station)
    print("Position:", result.current_route_position)
    print("Arrival delay:", result.current_arrival_delay)

    assert result.current_route_position == 3
    assert result.current_station == "BEQ"
    assert result.current_arrival_delay == 16

    print("PASS - Forward state update accepted.")

    # ---------------------------------------------------------
    # TEST 3: Backward movement rejection
    # ---------------------------------------------------------
    print("\nTEST 3: Backward train movement")

    state_backward = TrainState(
        train_number="12303",
        current_station="LLH",
        current_route_position=2,
        current_arrival_delay=14,
        current_departure_delay=16,
        current_time=datetime(2024, 9, 26, 8, 18)
    )

    try:
        manager.update_state(state_backward)

        # This line should never execute.
        assert False, "Backward movement was not rejected."

    except ValueError as error:
        print("Rejected:", error)
        print("PASS - Backward movement rejected.")

    # ---------------------------------------------------------
    # TEST 4: Train number change rejection
    # ---------------------------------------------------------
    print("\nTEST 4: Train number change")

    state_other_train = TrainState(
        train_number="99999",
        current_station="BLY",
        current_route_position=4,
        current_arrival_delay=10,
        current_departure_delay=12,
        current_time=datetime(2024, 9, 26, 8, 20)
    )

    try:
        manager.update_state(state_other_train)

        # This line should never execute.
        assert False, "Train number change was not rejected."

    except ValueError as error:
        print("Rejected:", error)
        print("PASS - Train number change rejected.")

    # ---------------------------------------------------------
    # TEST 5: Get latest state
    # ---------------------------------------------------------
    print("\nTEST 5: Retrieve latest valid state")

    current = manager.get_current_state()

    print("Train:", current.train_number)
    print("Station:", current.current_station)
    print("Position:", current.current_route_position)

    assert current.train_number == "12303"
    assert current.current_station == "BEQ"
    assert current.current_route_position == 3

    print("PASS - Latest state retrieved correctly.")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("ALL STAGE 12.1 TESTS PASSED")
    print("STAGE 12.1: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()