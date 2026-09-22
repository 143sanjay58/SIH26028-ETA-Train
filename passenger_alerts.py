class PassengerAlertGenerator:
    """
    Converts operational information into passenger-facing
    information without exposing internal operational details.
    """

    def generate(
        self,
        train_number,
        destination_station,
        predicted_eta,
        remaining_minutes,
        delay_status,
        confidence_level,
    ):
        if not train_number:
            raise ValueError("Train number is required.")
        if not destination_station:
            raise ValueError("Destination station is required.")
        if predicted_eta is None:
            raise ValueError("Predicted ETA is required.")
        if remaining_minutes < 0:
            raise ValueError("Remaining time cannot be negative.")

        if delay_status == "HEAVILY DELAYED":
            message = (
                f"Train {train_number} is heavily delayed. "
                f"Expected arrival at {destination_station}: {predicted_eta}."
            )
        elif delay_status == "DELAYED":
            message = (
                f"Train {train_number} is delayed. "
                f"Expected arrival at {destination_station}: {predicted_eta}."
            )
        elif delay_status == "SLIGHTLY DELAYED":
            message = (
                f"Train {train_number} is slightly delayed. "
                f"Expected arrival at {destination_station}: {predicted_eta}."
            )
        else:
            message = (
                f"Train {train_number} is expected to reach "
                f"{destination_station} at {predicted_eta}."
            )

        if confidence_level == "LOW":
            message += " ETA confidence is currently low."

        return {
            "train_number": train_number,
            "destination_station": destination_station,
            "predicted_eta": str(predicted_eta),
            "remaining_minutes": float(remaining_minutes),
            "delay_status": delay_status,
            "confidence_level": confidence_level,
            "message": message,
        }
