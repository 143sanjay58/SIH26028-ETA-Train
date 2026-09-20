STAGE 13 - OPERATIONAL INTELLIGENCE

Files:
1. eta_confidence.py
2. delay_impact.py
3. operational_alerts.py
4. passenger_alerts.py
5. stage13_pipeline.py
6. stage13_all_tests.py

Run:
    python stage13_all_tests.py

Important:
- The confidence value is an operational prototype indicator, not a calibrated probability.
- Stage 13 does not modify dynamic_eta_engine.py.
- stage13_pipeline.py accepts the existing ETA engine's result dictionary.
- The end-to-end test uses a representative ETA-engine result structure.
