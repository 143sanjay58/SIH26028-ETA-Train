from datetime import datetime

from train_state import TrainState
from train_state_manager import TrainStateManager
from state_change_detector import StateChangeDetector
from eta_refresh_trigger import ETARefreshTrigger
from dynamic_eta_engine import DynamicETAEngine


def get_station_from_result(result):
    """
    Get the station name from an ETA result.

    Different components may use different station-key names,
    so check the known possibilities.
    """

    station = result.get("station")

    if station is None:
        station = result.get("target_station")

    if station is None:
        station = result.get("to_station")

    if station is None:
        station = result.get("station_code")

    return station


def get_eta_from_result(result):
    """
    Get ETA value from an ETA result.
    """

    eta = result.get("eta")

    if eta is None:
        eta = result.get("predicted_eta")

    return eta


def run_tests():

    print("=" * 60)
    print("STAGE 12.5 - END-TO-END DYNAMIC UPDATE")
    print("=" * 60)

    # --------------------------------------------------
    # INITIALIZE COMPONENTS
    # --------------------------------------------------

    print("\nInitializing components...")

    manager = TrainStateManager()
    detector = StateChangeDetector()
    trigger = ETARefreshTrigger()

    eta_engine = DynamicETAEngine()

    print("PASS - All components initialized.")

    # --------------------------------------------------
    # STEP 1: INITIAL TRAIN STATE
    # --------------------------------------------------

    print("\nSTEP 1: Initial train state")

    state1 = TrainState(
        train_number="12303",
        current_station="LLH",
        current_route_position=2,
        current_arrival_delay=15,
        current_departure_delay=17,
        current_time=datetime(2024, 9, 26, 8, 10)
    )

    result_state1 = manager.update_state(state1)

    print("Train:", result_state1.train_number)
    print("Station:", result_state1.current_station)
    print("Position:", result_state1.current_route_position)
    print("Delay:", result_state1.current_arrival_delay)

    assert result_state1.train_number == "12303"
    assert result_state1.current_station == "LLH"
    assert result_state1.current_route_position == 2

    print("PASS - Initial train state accepted.")

    # --------------------------------------------------
    # STEP 2: INITIAL ETA CALCULATION
    # --------------------------------------------------

    print("\nSTEP 2: Calculate initial ETA")

    eta_result_1 = eta_engine.update_state(state1)

    print("Initial ETA results:", len(eta_result_1))

    assert len(eta_result_1) > 0

    first_result_1 = eta_result_1[0]

    first_station_1 = get_station_from_result(first_result_1)
    first_eta_1 = get_eta_from_result(first_result_1)

    print("First upcoming station:", first_station_1)
    print("Initial ETA:", first_eta_1)

    assert first_station_1 is not None
    assert first_eta_1 is not None

    print("PASS - Initial ETA calculated.")

    # --------------------------------------------------
    # STEP 3: UPDATED TRAIN STATE
    # --------------------------------------------------

    print("\nSTEP 3: Receive updated train state")

    state2 = TrainState(
        train_number="12303",
        current_station="BEQ",
        current_route_position=3,
        current_arrival_delay=16,
        current_departure_delay=18,
        current_time=datetime(2024, 9, 26, 8, 14)
    )

    result_state2 = manager.update_state(state2)

    print("Train:", result_state2.train_number)
    print("Station:", result_state2.current_station)
    print("Position:", result_state2.current_route_position)
    print("Delay:", result_state2.current_arrival_delay)

    assert result_state2.train_number == "12303"
    assert result_state2.current_station == "BEQ"
    assert result_state2.current_route_position == 3

    print("PASS - Updated train state accepted.")

    # --------------------------------------------------
    # STEP 4: DETECT STATE CHANGES
    # --------------------------------------------------

    print("\nSTEP 4: Detect state changes")

    changes = detector.detect_changes(
        state1,
        state2
    )

    print("Station changed:",
          changes["station_changed"])

    print("Position changed:",
          changes["position_changed"])

    print("Arrival delay changed:",
          changes["arrival_delay_changed"])

    print("Departure delay changed:",
          changes["departure_delay_changed"])

    print("Time changed:",
          changes["time_changed"])

    print("Any change:",
          changes["any_change"])

    assert changes["station_changed"] is True
    assert changes["position_changed"] is True
    assert changes["arrival_delay_changed"] is True
    assert changes["departure_delay_changed"] is True
    assert changes["time_changed"] is True
    assert changes["any_change"] is True

    print("PASS - State changes detected.")

    # --------------------------------------------------
    # STEP 5: CHECK ETA REFRESH
    # --------------------------------------------------

    print("\nSTEP 5: Check ETA refresh trigger")

    refresh_required = trigger.should_refresh(changes)

    print("ETA refresh required:", refresh_required)

    assert refresh_required is True

    print("PASS - ETA refresh triggered.")

    # --------------------------------------------------
    # STEP 6: RECALCULATE ETA
    # --------------------------------------------------

    print("\nSTEP 6: Recalculate ETA after state change")

    if refresh_required:

        eta_result_2 = eta_engine.update_state(state2)

    else:

        eta_result_2 = eta_result_1

    print("Updated ETA results:", len(eta_result_2))

    assert len(eta_result_2) > 0

    first_result_2 = eta_result_2[0]

    first_station_2 = get_station_from_result(first_result_2)
    first_eta_2 = get_eta_from_result(first_result_2)

    print("New first upcoming station:",
          first_station_2)

    print("Updated ETA:",
          first_eta_2)

    assert first_station_2 is not None
    assert first_eta_2 is not None

    print("PASS - ETA recalculated.")

    # --------------------------------------------------
    # STEP 7: VERIFY DYNAMIC UPDATE
    # --------------------------------------------------

    print("\nSTEP 7: Verify dynamic ETA update")

    print("\nInitial state:")
    print("  Station:", state1.current_station)
    print("  Position:", state1.current_route_position)
    print("  Delay:", state1.current_arrival_delay)

    print("\nUpdated state:")
    print("  Station:", state2.current_station)
    print("  Position:", state2.current_route_position)
    print("  Delay:", state2.current_arrival_delay)

    print("\nInitial ETA information:")
    print("  First station:", first_station_1)
    print("  ETA:", first_eta_1)

    print("\nUpdated ETA information:")
    print("  First station:", first_station_2)
    print("  ETA:", first_eta_2)

    # Train must move forward
    assert state2.current_route_position > \
           state1.current_route_position

    # Delay changed
    assert state2.current_arrival_delay != \
           state1.current_arrival_delay

    # Upcoming station should change because train moved
    assert first_station_2 != first_station_1

    # ETA should also change
    assert first_eta_2 != first_eta_1

    print("\nPASS - Dynamic ETA update verified.")

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ALL STAGE 12.5 TESTS PASSED")
    print("STAGE 12.5: PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()