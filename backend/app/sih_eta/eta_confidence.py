class ETAConfidence:
    """
    Prototype ETA confidence indicator.
    This is an operational indicator, not a calibrated probability.
    """

    def calculate(self, remaining_minutes, stations_ahead, current_delay):
        if remaining_minutes < 0:
            raise ValueError("Remaining time cannot be negative.")
        if stations_ahead < 0:
            raise ValueError("Stations ahead cannot be negative.")
        if current_delay < 0:
            raise ValueError("Current delay cannot be negative.")

        score = 100

        if remaining_minutes > 480:
            score -= 25
        elif remaining_minutes > 240:
            score -= 15
        elif remaining_minutes > 120:
            score -= 5

        if current_delay > 180:
            score -= 25
        elif current_delay > 120:
            score -= 15
        elif current_delay > 60:
            score -= 5

        if stations_ahead > 100:
            score -= 15
        elif stations_ahead > 50:
            score -= 10
        elif stations_ahead > 20:
            score -= 5

        score = max(0, min(100, score))

        if score >= 80:
            level = "HIGH"
        elif score >= 60:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "confidence_score": score,
            "confidence_level": level,
        }
