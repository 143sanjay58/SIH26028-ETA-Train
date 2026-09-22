from datetime import datetime
from train_state import TrainState


state = TrainState(
    train_number="12303",
    current_station="BWN",
    current_route_position=2,
    current_arrival_delay=15,
    current_departure_delay=17,
    current_time=datetime(2024, 9, 26, 9, 25)
)

print("Train Number:", state.train_number)
print("Current Station:", state.current_station)
print("Route Position:", state.current_route_position)
print("Arrival Delay:", state.current_arrival_delay, "minutes")
print("Departure Delay:", state.current_departure_delay, "minutes")
print("Current Time:", state.current_time)