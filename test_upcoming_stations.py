from upcoming_stations import UpcomingStationGenerator


TIMETABLE = r"ml_ready_segments_final.csv"


generator = UpcomingStationGenerator(TIMETABLE)

upcoming = generator.get_upcoming_stations(
    train_number="12303",
    current_route_position=2
)

print("\nUpcoming stations:")
print(upcoming.to_string(index=False))