class DelayImpactAnalyzer:
    """
    Converts the current delay and future ETA delay into
    an operational impact description.
    """

    def analyze(self, current_delay, predicted_delay, stations_ahead):
        if current_delay < 0:
            raise ValueError("Current delay cannot be negative.")
        if predicted_delay < 0:
            raise ValueError("Predicted delay cannot be negative.")
        if stations_ahead < 0:
            raise ValueError("Stations ahead cannot be negative.")

        change = predicted_delay - current_delay

        if predicted_delay <= 5:
            severity = "LOW"
        elif predicted_delay <= 15:
            severity = "MODERATE"
        elif predicted_delay <= 60:
            severity = "HIGH"
        else:
            severity = "CRITICAL"

        if change > 5:
            trend = "WORSENING"
        elif change < -5:
            trend = "IMPROVING"
        else:
            trend = "STABLE"

        if stations_ahead == 0:
            route_impact = "AT_DESTINATION"
        elif stations_ahead <= 5:
            route_impact = "NEAR_TERM"
        elif stations_ahead <= 20:
            route_impact = "MEDIUM_TERM"
        else:
            route_impact = "LONG_ROUTE"

        return {
            "current_delay": float(current_delay),
            "predicted_delay": float(predicted_delay),
            "delay_change": float(change),
            "severity": severity,
            "trend": trend,
            "route_impact": route_impact,
        }
