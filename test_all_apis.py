#!/usr/bin/env python3
"""Test all API endpoints for RAILPULSE AI (Railway Intelligence Platform)"""
import httpx
import json
import asyncio
import sys

BASE_URL = "http://localhost:8000"
TOKEN = None
RESULTS = []

def log(endpoint, method, status, detail=""):
    icon = "PASS" if 200 <= status < 400 else "FAIL"
    RESULTS.append((icon, f"{method:6s} {endpoint:50s} -> {status} {detail}"))
    print(RESULTS[-1][1])

def auth_header():
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

async def run():
    global TOKEN
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as c:

        # 1. Health
        r = await c.get("/api/health")
        log("/api/health", "GET", r.status_code, r.text[:120])

        # 2. Auth - Login
        r = await c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        log("/api/auth/login (admin)", "POST", r.status_code)
        if r.status_code == 200:
            TOKEN = r.json().get("access_token")
            print(f"    Token acquired: {TOKEN[:20]}...")

        # 3. Auth - Get current user
        r = await c.get("/api/auth/me", headers=auth_header())
        log("/api/auth/me", "GET", r.status_code, f"user={r.json().get('username','?')}" if r.status_code==200 else "")

        # 4. Auth - Login as passenger
        r2 = await c.post("/api/auth/login", json={"username": "passenger", "password": "passenger123"})
        log("/api/auth/login (passenger)", "POST", r2.status_code)

        # 5. Logout
        r = await c.post("/api/auth/logout", headers=auth_header())
        log("/api/auth/logout", "POST", r.status_code)

        # Re-login as admin for further tests
        r = await c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        if r.status_code == 200:
            TOKEN = r.json().get("access_token")

        # 6. Trains - List
        r = await c.get("/api/trains", headers=auth_header())
        log("/api/trains", "GET", r.status_code, f"count={r.json().get('total',0)}" if r.status_code==200 else "")

        # 7. Trains - Get by ID
        r = await c.get("/api/trains/1", headers=auth_header())
        log("/api/trains/1", "GET", r.status_code, f"train={r.json().get('train_number','?')}" if r.status_code==200 else "")

        # 8. Trains - Get by number
        r = await c.get("/api/trains/number/12345", headers=auth_header())
        log("/api/trains/number/12345", "GET", r.status_code, f"name={r.json().get('train_name','?')}" if r.status_code==200 else "")

        # 9. Trains - Live
        r = await c.get("/api/trains/1/live", headers=auth_header())
        log("/api/trains/1/live", "GET", r.status_code)

        # 10. Trains - Route
        r = await c.get("/api/trains/1/route", headers=auth_header())
        log("/api/trains/1/route", "GET", r.status_code)

        # 11. Trains - Positions
        r = await c.get("/api/trains/1/positions", headers=auth_header())
        log("/api/trains/1/positions", "GET", r.status_code, f"count={len(r.json())}" if r.status_code==200 else "")

        # 12. Trains - Events
        r = await c.get("/api/trains/1/events", headers=auth_header())
        log("/api/trains/1/events", "GET", r.status_code, f"count={len(r.json())}" if r.status_code==200 else "")

        # 13. Stations - List
        r = await c.get("/api/stations", headers=auth_header())
        log("/api/stations", "GET", r.status_code, f"count={r.json().get('total', len(r.json())) if isinstance(r.json(), dict) else len(r.json())}" if r.status_code==200 else "")

        # 14. Stations - Get by ID
        r = await c.get("/api/stations/1", headers=auth_header())
        log("/api/stations/1", "GET", r.status_code, f"name={r.json().get('name','?')}" if r.status_code==200 else "")

        # 15. Predictions - ETA
        r = await c.get("/api/predictions/eta/12345", headers=auth_header())
        log("/api/predictions/eta/12345", "GET", r.status_code)

        # 16. Predictions - POST ETA
        r = await c.post("/api/predictions/eta", json={"train_number": "12301", "include_explanations": True, "include_uncertainty": True}, headers=auth_header())
        log("/api/predictions/eta (POST)", "POST", r.status_code)

        # 17. Weather - Station
        r = await c.get("/api/weather/station/1", headers=auth_header())
        log("/api/weather/station/1", "GET", r.status_code, f"source={r.json().get('data_source','?')}" if r.status_code==200 else "")

        # 18. Weather - Coordinates
        r = await c.get("/api/weather/coordinates?lat=28.6401&lon=77.2153", headers=auth_header())
        log("/api/weather/coordinates", "GET", r.status_code)

        # 19. Weather - Route
        r = await c.get("/api/weather/route/1", headers=auth_header())
        log("/api/weather/route/1", "GET", r.status_code, f"count={len(r.json())}" if r.status_code==200 else "")

        # 20. Alerts
        r = await c.get("/api/alerts", headers=auth_header())
        log("/api/alerts", "GET", r.status_code)

        # 21. Congestion - Network
        r = await c.get("/api/congestion/network", headers=auth_header())
        log("/api/congestion/network", "GET", r.status_code)

        # 22. Simulation - Status
        r = await c.get("/api/simulation/status", headers=auth_header())
        log("/api/simulation/status", "GET", r.status_code, json.dumps(r.json())[:80] if r.status_code==200 else "")

        # 23. Simulation - Control (start)
        r = await c.post("/api/simulation/control", json={"action": "start"}, headers=auth_header())
        log("/api/simulation/control (start)", "POST", r.status_code)

        await asyncio.sleep(3)

        # 24. Simulation - Control (stop)
        r = await c.post("/api/simulation/control", json={"action": "stop"}, headers=auth_header())
        log("/api/simulation/control (stop)", "POST", r.status_code)

        # 25. Simulation - What-if
        r = await c.post("/api/simulation/what-if", json={"scenario": "CONGESTION", "parameters": {}}, headers=auth_header())
        log("/api/simulation/what-if", "POST", r.status_code)

        # Summary
        print("\n" + "="*80)
        passed = sum(1 for i, _ in RESULTS if i == "PASS")
        failed = sum(1 for i, _ in RESULTS if i == "FAIL")
        print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(RESULTS)} tests")
        if failed:
            print("\nFAILED ENDPOINTS:")
            for icon, msg in RESULTS:
                if icon == "FAIL":
                    print(f"  {msg}")
        print("="*80)
        return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run())
    sys.exit(0 if success else 1)
