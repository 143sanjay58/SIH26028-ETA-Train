from datetime import datetime, timedelta
from train_state import TrainState
from real_time_state_stream import RealTimeStateStream
from continuous_eta_monitor import ContinuousETAMonitor
from eta_change_history import ETAChangeHistory
from stage14_pipeline import Stage14Pipeline

class FakeStateManager:
    def __init__(self): self.current_state=None
    def update_state(self, s):
        if s is None: raise ValueError("Train state cannot be None.")
        if self.current_state and s.train_number != self.current_state.train_number:
            raise ValueError("Train number cannot change during a state update.")
        if self.current_state and s.current_route_position < self.current_state.current_route_position:
            raise ValueError("Train route position cannot move backwards.")
        self.current_state=s; return s
    def get_current_state(self): return self.current_state

class FakeDetector:
    def detect_changes(self, old, new):
        if old.train_number != new.train_number: raise ValueError("Train number cannot change during state comparison.")
        d={k:getattr(old,k)!=getattr(new,k) for k in
           ["current_station","current_route_position","current_arrival_delay","current_departure_delay","current_time"]}
        d["station_changed"]=d.pop("current_station")
        d["position_changed"]=d.pop("current_route_position")
        d["arrival_delay_changed"]=d.pop("current_arrival_delay")
        d["departure_delay_changed"]=d.pop("current_departure_delay")
        d["time_changed"]=d.pop("current_time"); d["any_change"]=any(d.values()); return d

class FakeTrigger:
    def should_refresh(self,c):
        return any(c.get(k,False) for k in ["station_changed","position_changed","arrival_delay_changed","departure_delay_changed"])

class FakeEngine:
    def update_state(self,s):
        return [{"station": f"S{p}", "eta": s.current_time + timedelta(minutes=10+p),
                 "remaining_minutes": 10+p, "future_arrival_delay": s.current_arrival_delay+2}
                for p in range(s.current_route_position, s.current_route_position+3)]

def make_states():
    t=datetime(2024,9,26,8,10)
    return [
      TrainState("12303","LLH",2,15,17,t),
      TrainState("12303","BEQ",3,16,18,t+timedelta(minutes=4)),
      TrainState("12303","BLY",4,19,21,t+timedelta(minutes=8)),
      TrainState("12303","BZL",5,17,19,t+timedelta(minutes=12)),
      TrainState("12303","DKAE",6,20,22,t+timedelta(minutes=16)),
    ]

def test_14_1():
    stream=RealTimeStateStream(make_states())
    assert stream.has_next()
    got=[]
    while stream.has_next(): got.append(stream.next_state().current_route_position)
    assert got==[2,3,4,5,6] and stream.next_state() is None
    stream.reset(); assert stream.next_state().current_route_position==2
    print("14.1 PASS - state stream sequencing/reset")

def test_14_2_14_3():
    sm,det,trig=FakeStateManager(),FakeDetector(),FakeTrigger()
    mon=ContinuousETAMonitor(sm,det,trig,FakeEngine())
    hist=ETAChangeHistory()
    prev=None
    for s in make_states():
        rec,etas,_=mon.process_state(s); hist.add(rec)
        assert rec["refresh_required"] is True
        assert rec["first_eta"] != prev if prev is not None else True
        prev=rec["first_eta"]
    assert len(hist.all())==5 and hist.eta_changed_count()==4
    print("14.2 PASS - continuous ETA monitor")
    print("14.3 PASS - ETA change history")

def test_14_4():
    sm,det,trig=FakeStateManager(),FakeDetector(),FakeTrigger()
    mon=ContinuousETAMonitor(sm,det,trig,FakeEngine())
    first=make_states()[0]
    mon.process_state(first)
    same=TrainState("12303","LLH",2,15,17,first.current_time+timedelta(minutes=1))
    rec,etas,_=mon.process_state(same)
    assert rec["refresh_required"] is False and etas is None
    changed=TrainState("12303","LLH",2,16,18,first.current_time+timedelta(minutes=2))
    rec,etas,_=mon.process_state(changed)
    assert rec["refresh_required"] is True and etas
    print("14.4 PASS - refresh only on relevant state changes")

def test_14_5():
    pipeline=Stage14Pipeline(FakeStateManager(),FakeDetector(),FakeTrigger(),FakeEngine())
    outputs=pipeline.run(make_states())
    assert len(outputs)==5
    assert all(x[0]["refresh_required"] for x in outputs)
    assert len(pipeline.history.all())==5
    path="stage14_continuous_eta_history.csv"
    pipeline.export_history(path)
    import os
    assert os.path.exists(path) and os.path.getsize(path)>0
    print("14.5 PASS - end-to-end continuous monitoring")
    print("History exported:",path)

if __name__=="__main__":
    print("="*60); print("STAGE 14 - CONTINUOUS ETA MONITORING"); print("="*60)
    test_14_1(); test_14_2_14_3(); test_14_4(); test_14_5()
    print("="*60); print("ALL STAGE 14 TESTS PASSED"); print("STAGE 14: COMPLETE"); print("="*60)
