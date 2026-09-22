STAGE 16 — FINAL VISUAL DASHBOARD

Purpose
-------
A browser dashboard for SIH26028 that presents:
- current train state
- delay status
- dynamic ETA timeline
- passenger journey assistance
- operational intelligence
- simulated continuous state updates
- optional connection to the existing FastAPI /predict-eta endpoint

IMPORTANT
---------
This dashboard does NOT replace or modify:
- dynamic_eta_engine.py
- feature_builder.py
- eta_predictor.py
- LightGBM model files

It is a presentation layer around the validated backend.

Run
---
1. Install Node.js (Node 22 is suitable for the existing project).
2. Open a terminal in this folder.
3. Run:
   npm install
   npm run dev
4. Open the Vite URL shown in the terminal.

API connection
--------------
Start the existing SIH26028 FastAPI backend first:
python -m uvicorn api:app --reload

Then use "REFRESH ETA FROM API".
If the API is unavailable, the dashboard automatically stays in demo simulation mode.

SIH DEMO FLOW
-------------
1. Open dashboard.
2. Show Train 12303 and current delay.
3. Click SIMULATE NEXT STATE repeatedly.
4. Explain that train position/delay changes trigger ETA refresh.
5. Show Dynamic ETA Timeline.
6. Show LLH → BZL passenger ETA.
7. Show operational intelligence.
8. If backend is running, click REFRESH ETA FROM API to demonstrate the real FastAPI connection.

Prototype/data note
-------------------
The dashboard uses simulated/recorded train states for demonstration.
Do not claim direct live access to Indian Railways GPS or operational systems unless such access has actually been provided.
