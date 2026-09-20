class RealTimeStateStream:
    """Provides sequential simulated/recorded TrainState updates."""
    def __init__(self, states):
        if states is None:
            raise ValueError("State stream cannot be None.")
        if not states:
            raise ValueError("State stream cannot be empty.")
        self.states = list(states)
        self.index = 0

    def has_next(self):
        return self.index < len(self.states)

    def next_state(self):
        if not self.has_next():
            return None
        state = self.states[self.index]
        self.index += 1
        return state

    def reset(self):
        self.index = 0
