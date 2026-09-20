class ETARefreshTrigger:
    """
    Determines whether the ETA system should refresh
    after a train-state update.
    """

    def should_refresh(self, changes):

        if changes is None:
            raise ValueError("Change information cannot be None.")

        # ETA should refresh when any train-state information
        # relevant to ETA has changed.
        relevant_changes = [
            changes.get("station_changed", False),
            changes.get("position_changed", False),
            changes.get("arrival_delay_changed", False),
            changes.get("departure_delay_changed", False)
        ]

        return any(relevant_changes)