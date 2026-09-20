def get_destination_eta(
    eta_results,
    destination_station
):
    """
    Finds the ETA result for the passenger's
    destination station.
    """

    destination_station = (
        destination_station
        .strip()
        .upper()
    )

    for result in eta_results:

        if not isinstance(result, dict):
            continue

        # ----------------------------------------------------
        # Find station code
        # ----------------------------------------------------

        station = result.get(
            "station"
        )

        if station is None:

            station = result.get(
                "target_station"
            )

        if station is None:

            station = result.get(
                "to_station"
            )

        if station is None:

            station = result.get(
                "station_code"
            )

        if station is None:
            continue

        station = (
            str(station)
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # Compare destination
        # ----------------------------------------------------

        if station == destination_station:

            # Create a normalized result
            normalized_result = dict(result)

            normalized_result["station"] = station

            # ------------------------------------------------
            # Normalize remaining time
            # ------------------------------------------------

            if "remaining_minutes" not in normalized_result:

                if "predicted_remaining_minutes" in result:

                    normalized_result["remaining_minutes"] = (
                        result["predicted_remaining_minutes"]
                    )

            return normalized_result

    return None