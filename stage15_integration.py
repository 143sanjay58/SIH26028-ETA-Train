from datetime import datetime, timedelta
import time
from train_state import TrainState
from stage14_pipeline import Stage14Pipeline
from unified_system import UnifiedSystem

class StateManager:
    def __init__(self): self.current_state = None
    def update_state(self, s):
        if s is None: raise ValueError("Train state cannot be None.")
        if self.current_state and s.train_number != self.current_state.train_number:
            raise ValueError("Train number cannot change during a state update.")
        if self.current_state and s.current_route_position < self.current_state.current_route_position:
            raise ValueError("Train route position cannot move backwards.")
        self.current_state = s
        return s
    def get_current_state(self): return self.current_state

class Detector:
    def detect_changes(self, old, new):
        if old is None or new is None: raise ValueError("States cannot be None.")
        if old.train_number != new.train_number: raise ValueError("Train number cannot change during comparison.")
        changes = {
            "station_changed": old.current_station != new.current_station,
            "position_changed": old.current_route_position != new.current_route_position,
            "arrival_delay_changed": old.current_arrival_delay != new.current_arrival_delay,
            "departure_delay_changed": old.current_departure_delay != new.current_departure_delay,
            "time_changed": old.current_time != new.current_time,
        }
        changes["any_change"] = any(changes.values())
        return changes

class Trigger:
    def should_refresh(self, changes):
        if changes is None: raise ValueError("Change information cannot be None.")
        return any(changes.get(k, False) for k in ("station_changed", "position_changed", "arrival_delay_changed", "departure_delay_changed"))

class IntegratedETASimulator:
    """Deterministic stand-in for the already validated ETA engine interface.
    It mirrors the interface only; it is not the production LightGBM engine."""
    def update_state(self, state):
        base = 8.65 + max(0, state.current_route_position - 2) * 0.85
        return [
            {"station": f"UPCOMING_{i}", "eta": state.current_time + timedelta(minutes=base + i * 3.0),
             "remaining_minutes": round(base + i * 3.0, 2),
             "future_arrival_delay": round(max(0, state.current_arrival_delay) + 4.0 + i * 0.5, 2)}
            for i in range(1, 4)
        ]

class OperationalAdapter:
    def process(self, current_delay, predicted_delay, remaining_minutes, stations_ahead):
        change = predicted_delay - current_delay
        if predicted_delay <= 5: severity = "LOW"
        elif predicted_delay <= 15: severity = "MODERATE"
        elif predicted_delay <= 60: severity = "HIGH"
        else: severity = "CRITICAL"
        if change > 5: trend = "WORSENING"
        elif change < -5: trend = "IMPROVING"
        else: trend = "STABLE"
        score = 100
        if remaining_minutes > 480: score -= 25
        elif remaining_minutes > 240: score -= 15
        elif remaining_minutes > 120: score -= 5
        if current_delay > 180: score -= 25
        elif current_delay > 120: score -= 15
        elif current_delay > 60: score -= 5
        if stations_ahead > 100: score -= 15
        elif stations_ahead > 50: score -= 10
        elif stations_ahead > 20: score -= 5
        score = max(0, min(100, score))
        level = "HIGH" if score >= 80 else "MEDIUM" if score >= 60 else "LOW"
        return {"severity": severity, "trend": trend, "confidence_score": score, "confidence_level": level,
                "passenger_message": f"Current delay: {current_delay:.1f} minutes. Predicted delay: {predicted_delay:.1f} minutes."}

def make_states(position_start=2, count=5, delay_start=15):
    t = datetime(2024, 9, 26, 8, 10)
    stations = ["LLH", "BEQ", "BLY", "BZL", "DKAE", "JOX", "GBRA"]
    return [TrainState("12303", stations[i], position_start+i, delay_start + [0,1,4,2,5][i % 5],
                       delay_start + [2,3,6,4,7][i % 5], t + timedelta(minutes=4*i)) for i in range(count)]

def build_system():
    pipeline = Stage14Pipeline(StateManager(), Detector(), Trigger(), IntegratedETASimulator(), OperationalAdapter())
    return UnifiedSystem(pipeline)

def run_all_tests():
    print("="*68); print("STAGE 15 - SYSTEM INTEGRATION & FINAL PROTOTYPE VALIDATION"); print("="*68)

    # 15.1 Full integration
    system = build_system()
    result = system.process_states(make_states())
    assert len(result) == 5
    assert all(x["status"] == "OK" for x in result)
    assert all("current_state" in x and "eta" in x and "operational_intelligence" in x for x in result)
    print("15.1 PASS - full system integration")

    # 15.2 Unified response
    x = result[-1]
    assert x["train_number"] == "12303"
    assert x["eta"]["predicted_eta"] is not None
    assert x["operational_intelligence"]["severity"] in {"LOW","MODERATE","HIGH","CRITICAL"}
    print("15.2 PASS - unified API-style response")

    # 15.3 Scenarios
    early = build_system().process_states(make_states(2, 2, 5))
    middle = build_system().process_states(make_states(100, 2, 40))
    late = build_system().process_states(make_states(232, 2, 80))
    for scenario in (early, middle, late):
        assert len(scenario) == 2 and all(s["eta"]["predicted_eta"] for s in scenario)
    print("15.3 PASS - early/middle/late scenarios")

    # 15.4 Failure/edge cases
    try: build_system().process_states([]); raise AssertionError("empty states accepted")
    except ValueError: pass
    try: build_system().process_states([TrainState("12303","LLH",2,15,17,datetime.now()), TrainState("99999","BEQ",3,16,18,datetime.now())]); raise AssertionError("train switch accepted")
    except ValueError: pass
    try: build_system().process_states([TrainState("12303","LLH",2,15,17,datetime.now()), TrainState("12303","BEQ",1,16,18,datetime.now())]); raise AssertionError("backward route accepted")
    except ValueError: pass
    print("15.4 PASS - failure and edge-case handling")

    # 15.5 performance smoke test
    t0 = time.perf_counter()
    for _ in range(100):
        build_system().process_states(make_states())
    elapsed = time.perf_counter() - t0
    avg_ms = elapsed / 100 * 1000
    assert avg_ms < 100
    print(f"15.5 PASS - performance smoke test ({avg_ms:.3f} ms/run)")

    # 15.6 validation report
    checks = [
        ("integration", True), ("unified_response", True), ("scenarios", True),
        ("edge_cases", True), ("performance_smoke", True)
    ]
    with open("stage15_validation_report.csv", "w", encoding="utf-8") as f:
        f.write("check,status\n")
        for name, ok in checks: f.write(f"{name},{'PASS' if ok else 'FAIL'}\n")
    print("15.6 PASS - final validation report generated")

    # 15.7 demo snapshot
    demo = result[-1]
    with open("stage15_demo_snapshot.json", "w", encoding="utf-8") as f:
        import json; json.dump(demo, f, indent=2, default=str)
    print("15.7 PASS - SIH demonstration snapshot generated")

    print("="*68); print("ALL STAGE 15 TESTS PASSED"); print("STAGE 15: COMPLETE"); print("="*68)
    return avg_ms

if __name__ == "__main__": run_all_tests()
