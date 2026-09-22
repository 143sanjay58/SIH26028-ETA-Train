from dataclasses import dataclass


@dataclass
class PassengerRequest:
    """
    Stores the passenger's journey information.
    """

    train_number: str
    boarding_station: str
    destination_station: str