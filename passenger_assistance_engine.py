from passenger_eta import get_destination_eta
from passenger_status import get_delay_status


def create_assistance_response(
    passenger,
    eta_results,
    current_arrival_delay
):
    """
    Creates the final passenger assistance response.

    The ETA results come from the Dynamic ETA Engine.
    """

    # --------------------------------------------------------
    # Find passenger destination
    # --------------------------------------------------------

    destination_result = get_destination_eta(
        eta_results,
        passenger.destination_station
    )

    # --------------------------------------------------------
    # Destination not found
    # --------------------------------------------------------

    if destination_result is None:

        return {
            "status": "DESTINATION_NOT_FOUND",

            "train_number":
                passenger.train_number,

            "boarding_station":
                passenger.boarding_station,

            "destination_station":
                passenger.destination_station,

            "message":
                "Destination is not available "
                "in the upcoming route."
        }

    # --------------------------------------------------------
    # Get ETA
    # --------------------------------------------------------

    predicted_eta = destination_result.get(
        "eta"
    )

    # --------------------------------------------------------
    # Get remaining time
    # --------------------------------------------------------

    remaining_minutes = destination_result.get(
        "remaining_minutes"
    )

    if remaining_minutes is None:

        remaining_minutes = destination_result.get(
            "predicted_remaining_minutes"
        )

    # --------------------------------------------------------
    # Convert remaining time to float
    # --------------------------------------------------------

    if remaining_minutes is not None:

        remaining_minutes = float(
            remaining_minutes
        )

    # --------------------------------------------------------
    # Current train delay status
    # --------------------------------------------------------

    delay_status = get_delay_status(
        current_arrival_delay
    )

    # --------------------------------------------------------
    # Final passenger response
    # --------------------------------------------------------

    return {

        "status": "OK",

        "train_number":
            passenger.train_number,

        "boarding_station":
            passenger.boarding_station,

        "destination_station":
            passenger.destination_station,

        "current_delay_minutes":
            current_arrival_delay,

        "delay_status":
            delay_status,

        "predicted_eta":
            predicted_eta,

        "remaining_minutes":
            remaining_minutes,

        "message":
            (
                f"Train {passenger.train_number} "
                f"is currently "
                f"{delay_status.lower()} "
                f"with a delay of "
                f"{current_arrival_delay} minutes. "
                f"It is expected to reach "
                f"{passenger.destination_station} "
                f"at {predicted_eta}. "
                f"Estimated remaining time: "
                f"{remaining_minutes:.2f} minutes."
            )
    }