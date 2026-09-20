from real_time_state_stream import RealTimeStateStream
from continuous_eta_monitor import ContinuousETAMonitor
from eta_change_history import ETAChangeHistory

class Stage14Pipeline:
    """End-to-end continuous monitoring coordinator."""
    def __init__(self, state_manager, change_detector, refresh_trigger,
                 eta_engine, operational_pipeline=None):
        self.stream_components = (state_manager, change_detector, refresh_trigger)
        self.monitor = ContinuousETAMonitor(
            state_manager, change_detector, refresh_trigger,
            eta_engine, operational_pipeline
        )
        self.history = ETAChangeHistory()

    def run(self, states):
        stream = RealTimeStateStream(states)
        outputs = []
        while stream.has_next():
            record, eta_results, operational = self.monitor.process_state(stream.next_state())
            self.history.add(record)
            outputs.append((record, eta_results, operational))
        return outputs

    def export_history(self, path):
        self.history.export_csv(path)
