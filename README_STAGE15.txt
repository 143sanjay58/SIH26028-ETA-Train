STAGE 15 — SYSTEM INTEGRATION & FINAL PROTOTYPE VALIDATION

Purpose
-------
Stage 15 verifies that the major prototype layers can operate as one
coherent system: train state -> state management -> change detection ->
refresh decision -> ETA processing -> operational intelligence -> unified
response.

15.1 Full System Integration
15.2 Unified API-style Response
15.3 Early/Middle/Late Route Scenarios
15.4 Failure and Edge-Case Testing
15.5 Performance Smoke Test
15.6 Final Validation Report
15.7 SIH Demonstration Snapshot

Important prototype boundary
-----------------------------
This package validates the integration interfaces using a deterministic
ETA simulator. It does NOT replace the already validated production
LightGBM ETA engine in the user's D:\SIH-2026 project, and it does not
claim direct live access to Indian Railways systems. The production engine
can be plugged into the same interface: update_state(TrainState) -> ETA
results.

No change is made to dynamic_eta_engine.py.
