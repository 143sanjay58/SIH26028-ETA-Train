class TrainStateManager:
    """
    Maintains the latest valid state of a train.
    """

    def __init__(self):
        self.current_state = None

    def update_state(self, new_state):
        """
        Store a new train state.
        """

        if new_state is None:
            raise ValueError("Train state cannot be None.")

        # If a previous state exists, make sure the train
        # is not moving backwards on its route.
        if self.current_state is not None:

            if new_state.train_number != self.current_state.train_number:
                raise ValueError(
                    "Train number cannot change during a state update."
                )

            if (
                new_state.current_route_position
                < self.current_state.current_route_position
            ):
                raise ValueError(
                    "Train route position cannot move backwards."
                )

        self.current_state = new_state

        return self.current_state

    def get_current_state(self):
        """
        Return the latest train state.
        """

        return self.current_state