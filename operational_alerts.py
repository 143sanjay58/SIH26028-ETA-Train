class OperationalAlertGenerator:
    """
    Generates non-automated operational alerts.
    These are informational alerts for authorized operators.
    """

    def generate(self, delay_impact, confidence):
        if delay_impact is None:
            raise ValueError("Delay impact cannot be None.")
        if confidence is None:
            raise ValueError("Confidence cannot be None.")

        alerts = []

        severity = delay_impact["severity"]
        trend = delay_impact["trend"]
        confidence_level = confidence["confidence_level"]

        if severity == "CRITICAL":
            alerts.append({
                "type": "CRITICAL_DELAY",
                "priority": "HIGH",
                "message": "Predicted delay is critically high."
            })
        elif severity == "HIGH":
            alerts.append({
                "type": "HIGH_DELAY",
                "priority": "MEDIUM",
                "message": "Predicted delay is high."
            })
        elif severity == "MODERATE":
            alerts.append({
                "type": "MODERATE_DELAY",
                "priority": "LOW",
                "message": "Train is expected to remain moderately delayed."
            })

        if trend == "WORSENING":
            alerts.append({
                "type": "DELAY_WORSENING",
                "priority": "MEDIUM",
                "message": "Predicted delay is increasing."
            })
        elif trend == "IMPROVING":
            alerts.append({
                "type": "DELAY_IMPROVING",
                "priority": "INFO",
                "message": "Predicted delay is decreasing."
            })

        if confidence_level == "LOW":
            alerts.append({
                "type": "LOW_ETA_CONFIDENCE",
                "priority": "MEDIUM",
                "message": "ETA confidence is low; monitor the train state closely."
            })

        if not alerts:
            alerts.append({
                "type": "NORMAL_OPERATION",
                "priority": "INFO",
                "message": "No significant operational alert."
            })

        return alerts
