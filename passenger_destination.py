def find_destination(upcoming_stations, destination_station):
    """
    Check whether the passenger's destination
    is present in the upcoming station list.
    """

    destination_station = destination_station.upper()

    for station in upcoming_stations:

        if station.upper() == destination_station:
            return True

    return False