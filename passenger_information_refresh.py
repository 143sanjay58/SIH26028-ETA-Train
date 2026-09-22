class PassengerInformationRefresh:

    def refresh(self, passenger_request, journey_result):

        if passenger_request is None:
            raise ValueError("Passenger request cannot be None.")

        if journey_result is None:
            raise ValueError("Journey result cannot be None.")

        return {
            "train_number": passenger_request.train_number,
            "boarding_station": passenger_request.boarding_station,
            "destination_station": passenger_request.destination_station,
            "predicted_eta": journey_result.get("predicted_eta"),
            "remaining_minutes": journey_result.get("remaining_minutes"),
            "arrival_status": journey_result.get("arrival_status"),
            "connection_status": journey_result.get("connection_status")
        }