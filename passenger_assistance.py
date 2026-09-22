from passenger_eta import get_destination_eta


def create_passenger_assistance(
    passenger,
    eta_results
):
    """
    Create a passenger-friendly journey assistance response.
    """

    destination_result = get_destination_eta(
        eta_results,
        passenger.destination_station
    )

    # Destination not found
    if destination_result is None:

        return {
            "status": "DESTINATION_NOT_FOUND",
            "message": (
                "Destination station is not "
                "available in the upcoming route."
            )
        }

    # Extract ETA information
    eta = destination_result.get("eta")

    remaining_minutes = destination_result.get(
        "remaining_minutes"
    )

    # Build passenger response
    response = {

        "status": "OK",

        "train_number":
            passenger.train_number,

        "boarding_station":
            passenger.boarding_station,

        "destination_station":
            passenger.destination_station,

        "predicted_eta":
            eta,

        "remaining_minutes":
            remaining_minutes,

        "message":
            (
                f"Train {passenger.train_number} "
                f"is expected to reach "
                f"{passenger.destination_station} "
                f"at {eta}. "
                f"Estimated remaining time: "
                f"{remaining_minutes:.2f} minutes."
            )
    }

    return response