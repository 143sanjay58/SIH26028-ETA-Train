class ContinuousETAMonitor:
    """
    Processes incoming train states and refreshes ETA only when
    station/position/delay information changes.
    """
    def __init__(self, state_manager, change_detector, refresh_trigger,
                 eta_engine, operational_pipeline=None):
        self.state_manager = state_manager
        self.change_detector = change_detector
        self.refresh_trigger = refresh_trigger
        self.eta_engine = eta_engine
        self.operational_pipeline = operational_pipeline
        self.history = []

    def process_state(self, new_state):
        old_state = self.state_manager.get_current_state()

        if old_state is None:
            self.state_manager.update_state(new_state)
            eta_results = self.eta_engine.update_state(new_state)
            refreshed = True
            changes = {
                "station_changed": True,
                "position_changed": True,
                "arrival_delay_changed": True,
                "departure_delay_changed": True,
                "time_changed": True,
                "any_change": True
            }
        else:
            changes = self.change_detector.detect_changes(old_state, new_state)
            refreshed = self.refresh_trigger.should_refresh(changes)
            self.state_manager.update_state(new_state)
            eta_results = self.eta_engine.update_state(new_state) if refreshed else None

        first_eta = None
        first_remaining = None
        if eta_results:
            first = eta_results[0]
            first_eta = first.get("eta", first.get("predicted_eta"))
            first_remaining = first.get("remaining_minutes")
            if first_remaining is None:
                first_remaining = first.get("predicted_remaining_minutes")

        operational = None
        if self.operational_pipeline is not None and eta_results:
            operational = self.operational_pipeline.process(
                current_delay=float(new_state.current_arrival_delay),
                predicted_delay=float(
                    eta_results[0].get("predicted_future_arrival_delay",
                    eta_results[0].get("future_arrival_delay",
                    eta_results[0].get("predicted_delay", new_state.current_arrival_delay)))
                ),
                remaining_minutes=float(first_remaining or 0),
                stations_ahead=max(0, len(eta_results))
            )

        record = {
            "update_number": len(self.history) + 1,
            "train_number": new_state.train_number,
            "station": new_state.current_station,
            "route_position": new_state.current_route_position,
            "current_arrival_delay": new_state.current_arrival_delay,
            "current_departure_delay": new_state.current_departure_delay,
            "current_time": new_state.current_time.isoformat(),
            "refresh_required": refreshed,
            "eta_result_count": len(eta_results) if eta_results else 0,
            "first_eta": str(first_eta) if first_eta is not None else None,
            "first_remaining_minutes": first_remaining,
            "operational_update_generated": operational is not None
        }
        self.history.append(record)
        return record, eta_results, operational

    def get_history(self):
        return list(self.history)

    def reset_history(self):
        self.history.clear()
