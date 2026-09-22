STAGE 14 — REAL-TIME DATA SIMULATION & CONTINUOUS ETA MONITORING

Purpose
-------
Stage 14 demonstrates how a train-state stream can continuously feed the
ETA system. It uses simulated/recorded states and does not claim direct
live access to Indian Railways GPS or operational systems.

Components
----------
14.1 Real-Time State Stream Simulator
14.2 Continuous ETA Monitor
14.3 ETA Change History
14.4 Continuous Passenger/Operational Refresh Trigger
14.5 Full End-to-End Continuous Monitoring Test

Flow
----
State Stream
 -> State Manager
 -> Change Detector
 -> ETA Refresh Trigger
 -> Dynamic ETA Engine
 -> ETA History
 -> Passenger/Operational information

Important integration note
---------------------------
The monitor is designed around the existing Stage 12 interfaces and does
not modify dynamic_eta_engine.py. For deployment, instantiate it with the
project's real TrainStateManager, StateChangeDetector, ETARefreshTrigger,
and DynamicETAEngine objects.

Prototype test
--------------
The included test uses lightweight test doubles for the existing Stage 12
interfaces so the complete Stage 14 logic can be validated independently.
This avoids changing or depending on the user's local D:\SIH-2026 files.

Generated artifact
------------------
stage14_continuous_eta_history.csv

All Stage 14 tests pass in the packaged prototype.
