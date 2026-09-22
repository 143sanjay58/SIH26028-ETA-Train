class StateChangeDetector:
    """
    Detects changes between two train states.
    """

    def detect_changes(self, old_state, new_state):

        if old_state is None:
            raise ValueError("Old train state cannot be None.")

        if new_state is None:
            raise ValueError("New train state cannot be None.")

        if old_state.train_number != new_state.train_number:
            raise ValueError(
                "Train number cannot change during state comparison."
            )

        changes = {
            "station_changed": (
                old_state.current_station
                != new_state.current_station
            ),

            "position_changed": (
                old_state.current_route_position
                != new_state.current_route_position
            ),

            "arrival_delay_changed": (
                old_state.current_arrival_delay
                != new_state.current_arrival_delay
            ),

            "departure_delay_changed": (
                old_state.current_departure_delay
                != new_state.current_departure_delay
            ),

            "time_changed": (
                old_state.current_time
                != new_state.current_time
            )
        }

        changes["any_change"] = any(changes.values())

        return changes