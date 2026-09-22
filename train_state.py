from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrainState:
    train_number: str
    current_station: str
    current_route_position: int
    current_arrival_delay: float
    current_departure_delay: float
    current_time: datetime

