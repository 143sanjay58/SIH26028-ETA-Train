from datetime import datetime

class UnifiedSystem:
    """Stage 15 integration facade for the prototype."""
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def process_states(self, states):
        outputs = self.pipeline.run(states)
        unified = []
        for record, eta_results, operational in outputs:
            first = eta_results[0] if eta_results else {}
            unified.append({
                "status": "OK",
                "train_number": record["train_number"],
                "current_state": {
                    "station": record["station"],
                    "route_position": record["route_position"],
                    "arrival_delay_minutes": record["current_arrival_delay"],
                    "departure_delay_minutes": record["current_departure_delay"],
                    "current_time": record["current_time"],
                },
                "eta": {
                    "first_upcoming_station": first.get("station", first.get("target_station")),
                    "predicted_eta": record["first_eta"],
                    "remaining_minutes": record["first_remaining_minutes"],
                    "upcoming_station_count": record["eta_result_count"],
                },
                "operational_intelligence": operational,
                "refresh_required": record["refresh_required"],
            })
        return unified
