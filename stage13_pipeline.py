from eta_confidence import ETAConfidence
from delay_impact import DelayImpactAnalyzer
from operational_alerts import OperationalAlertGenerator
from passenger_alerts import PassengerAlertGenerator


class Stage13Pipeline:
    """
    Integrates the Stage 13 intelligence layers.
    It accepts an ETA-engine result and produces operational
    and passenger-facing information.
    """

    def __init__(self):
        self.confidence = ETAConfidence()
        self.impact = DelayImpactAnalyzer()
        self.operational_alerts = OperationalAlertGenerator()
        self.passenger_alerts = PassengerAlertGenerator()

    def process(
        self,
        train_number,
        destination_station,
        eta_result,
        current_delay,
        delay_status,
    ):
        if eta_result is None:
            raise ValueError("ETA result cannot be None.")

        remaining_minutes = float(
            eta_result.get("remaining_minutes", eta_result.get("predicted_remaining_minutes"))
        )
        stations_ahead = int(
            eta_result.get("stations_ahead", 0)
        )
        predicted_delay = float(
            eta_result.get("future_arrival_delay", eta_result.get("predicted_future_delay", current_delay))
        )
        predicted_eta = eta_result.get("eta", eta_result.get("predicted_eta"))

        if predicted_eta is None:
            raise ValueError("ETA result does not contain an ETA.")

        confidence = self.confidence.calculate(
            remaining_minutes,
            stations_ahead,
            current_delay,
        )

        impact = self.impact.analyze(
            current_delay,
            predicted_delay,
            stations_ahead,
        )

        operational = self.operational_alerts.generate(
            impact,
            confidence,
        )

        passenger = self.passenger_alerts.generate(
            train_number,
            destination_station,
            predicted_eta,
            remaining_minutes,
            delay_status,
            confidence["confidence_level"],
        )

        return {
            "train_number": train_number,
            "destination_station": destination_station,
            "confidence": confidence,
            "delay_impact": impact,
            "operational_alerts": operational,
            "passenger_information": passenger,
        }
