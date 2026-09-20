#!/usr/bin/env python
# -*- coding: utf-8 -*-
# WINDOWS_CONSOLE_UTF8_FIX: reconfigure stdout/stderr so unicode
# prints survive the default cp1252 Windows console.
import io
import sys
import urllib.error

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace"
)
sys.stderr = io.TextIOWrapper(
    sys.stderr.buffer, encoding="utf-8", errors="replace"
)

from role_auth import (
    AuthService,
    ROLE_PASSENGER,
    ROLE_CONTROL_ROOM,
    ROLE_CO_PILOT,
)
from operational_events import (
    ALLOWED_REASONS,
    OperationalEventStore,
    priority_for_delay,
)

# ============================================================
# SIH26028 - STAGE 17 TESTS
# Role-based auth + co-pilot delay reports + control room flow.
# Plain assertion script (same pattern as prior stages):
#   python stage17_all_tests.py
# Each section prints PASS.
# ============================================================

FIXTURE_TRAINS = {"12303", "12304"}

FIXTURE_STATIONS = {
    "12303": {"LLH", "BEQ", "BLY", "BZL", "DKAE"},
    "12304": {"HWH", "SRC", "BDC"},
}

# ============================================================
# 1. AUTH
# ============================================================

def test_auth():
    svc = AuthService()

    # All three demo accounts log in and receive a token.
    for role in (
        ROLE_PASSENGER,
        ROLE_CONTROL_ROOM,
        ROLE_CO_PILOT,
    ):
        user = {ROLE_PASSENGER: "passenger123",
                ROLE_CONTROL_ROOM: "control123",
                ROLE_CO_PILOT: "copilot123"}[role]
        session = svc.login(user, user)
        assert session["role"] == role
        assert len(session["token"]) == 32
        assert svc.verify_token(session["token"])["username"] == user

    # Invalid credentials are rejected.
    try:
        svc.login("nobody", "wrong")
        raise AssertionError("bad credentials accepted")
    except ValueError:
        pass

    # require_role honors the allowed list.
    session = svc.login("passenger123", "passenger123")
    me = svc.require_role(session["token"], [ROLE_PASSENGER])
    assert me["role"] == ROLE_PASSENGER

    try:
        svc.require_role(session["token"], [ROLE_CONTROL_ROOM])
        raise AssertionError("wrong-role access allowed")
    except ValueError:
        pass

    try:
        svc.require_role("not-a-token", [ROLE_PASSENGER])
        raise AssertionError("unknown token accepted")
    except ValueError:
        pass

    # Logout invalidates the token.
    svc.logout(session["token"])
    assert svc.verify_token(session["token"]) is None

    print("PASS auth (login, verify, require_role, logout)")


# ============================================================
# 2. DELAY REPORT STORE
# ============================================================

def test_report_store():
    store = OperationalEventStore(
        train_numbers=FIXTURE_TRAINS,
        route_station_map=FIXTURE_STATIONS,
    )

    report = store.create_report(
        train_number="12303",
        copilot_id="copilot123",
        current_station="BEQ",
        current_delay_minutes=17.0,
        reason="signal_issue",
        message="Signal clearance delayed departure from BEQ.",
    )
    assert report["status"] == "NEW"
    assert report["reason"] == "SIGNAL_ISSUE"
    assert report["train_number"] == "12303"
    assert report["ml_models_modified"] is False
    assert report["priority"] == "HIGH"
    assert store.get_report(report["report_id"]) is not None

    # Latest report for the train is the one just created.
    assert store.latest_report_for_train("12303")["report_id"] == report["report_id"]

    # Acknowledge flips status and records who/when.
    ack = store.acknowledge(report["report_id"], "control123")
    assert ack["status"] == "ACKNOWLEDGED"
    assert ack["acknowledged_by"] == "control123"
    assert ack["acknowledged_at"] is not None

    # Listing filters by status.
    assert any(r["status"] == "ACKNOWLEDGED" for r in store.list_reports(status="ACKNOWLEDGED"))
    assert not any(r["status"] == "NEW" for r in store.list_reports(status="ACKNOWLEDGED"))

    print("PASS delay report store (create, get, ack, list)")


# ============================================================
# 3. VALIDATION ERRORS
# ============================================================

def test_validation_errors():
    store = OperationalEventStore(
        train_numbers=FIXTURE_TRAINS,
        route_station_map=FIXTURE_STATIONS,
    )

    def expect_value_error(kwargs):
        try:
            store.create_report(
                train_number=kwargs.get("train_number", "12303"),
                copilot_id=kwargs.get("copilot_id", "copilot123"),
                current_station=kwargs.get("current_station", "BEQ"),
                current_delay_minutes=kwargs.get("current_delay_minutes", 5.0),
                reason=kwargs.get("reason", "SIGNAL_ISSUE"),
                message=kwargs.get("message", "Testing validation."),
            )
            raise AssertionError(f"expected ValueError for {kwargs}")
        except ValueError:
            pass

    expect_value_error({"train_number": "99999"})
    expect_value_error({"train_number": ""})
    expect_value_error({"current_station": "XYZ"})
    expect_value_error({"current_station": ""})
    expect_value_error({"current_delay_minutes": -1})
    expect_value_error({"current_delay_minutes": "abc"})
    expect_value_error({"reason": "BANANA"})
    expect_value_error({"reason": ""})
    expect_value_error({"message": ""})
    expect_value_error({"message": "x" * 501})

    # Station belongs to the wrong train.
    expect_value_error({"train_number": "12304", "current_station": "BEQ"})

    try:
        store.acknowledge("missing-report-id", "control123")
        raise AssertionError("acknowledge accepted an unknown report")
    except ValueError:
        pass

    print("PASS validation (unknown train, station, reason, delays, message)")


# ============================================================
# 4. PRIORITY THRESHOLDS
# ============================================================

def test_priorities():
    expectations = [
        (0.0, "LOW"),
        (5.0, "LOW"),
        (6.0, "MODERATE"),
        (15.0, "MODERATE"),
        (16.0, "HIGH"),
        (60.0, "HIGH"),
        (61.0, "CRITICAL"),
    ]
    for delay, expected in expectations:
        assert priority_for_delay(delay) == expected, (delay, expected)

    assert len(ALLOWED_REASONS) == 7
    for reason in (
        "SIGNAL_ISSUE",
        "TRACK_OBSTRUCTION",
        "TECHNICAL_ISSUE",
        "OPERATIONAL_ISSUE",
        "PASSENGER_ISSUE",
        "WEATHER_ISSUE",
        "OTHER",
    ):
        assert reason in ALLOWED_REASONS

    print("PASS priority thresholds + allowed reasons")


# ============================================================
# 5. FROZEN ROUTE INDEX (real dataset)
# ============================================================

def test_route_index():
    import role_api

    index = role_api.ROUTE_INDEX
    assert len(index["train_numbers"]) > 5000
    assert "12303" in index["train_numbers"]
    assert index["route_lengths"]["12303"] > 100
    assert "BEQ" in index["route_station_map"]["12303"]

    # Demo state + demo route are present.
    assert role_api.DEMO_STATES["12303"]["current_station"] == "BEQ"
    assert role_api.DEMO_ROUTES["12303"][0] == "LLH"

    print("PASS frozen route index (trains, stations, demo 12303)")


# ============================================================
# 6. LIVE ENDPOINT CHECKS (optional — skipped when API is down)
# ============================================================

def test_live_endpoints():
    import json
    import urllib.error
    import urllib.request

    BASE = "http://127.0.0.1:8000"

    def call(method, path, payload=None, token=None):
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            BASE + path, data=data, headers=headers, method=method
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())

    status, body = call("GET", "/health")
    assert status == 200 and body.get("eta_engine_loaded") is True

    # Login.
    status, copilot = call("POST", "/login", {
        "username": "copilot123", "password": "copilot123",
    })
    assert status == 200 and copilot["role"] == "CO_PILOT"

    status, control = call("POST", "/login", {
        "username": "control123", "password": "control123",
    })
    assert status == 200 and control["role"] == "CONTROL_ROOM"

    try:
        call("POST", "/login", {"username": "bad", "password": "bad"})
        raise AssertionError("bad login accepted")
    except urllib.error.HTTPError as err:
        assert err.code == 401

    # Co-pilot submits a report (role enforced).
    status, report = call(
        "POST", "/copilot/delay-report",
        {
            "train_number": "12303",
            "current_station": "BEQ",
            "current_delay_minutes": 18.0,
            "reason": "SIGNAL_ISSUE",
            "message": "Live endpoint test: signal section restored, delay continuing.",
        },
        token=copilot["token"],
    )
    assert status == 200 and report["status"] == "NEW"

    # Control room sees it and acknowledges.
    status, listing = call("GET", "/control-room/reports", token=control["token"])
    assert status == 200
    assert any(r["report_id"] == report["report_id"] for r in listing["reports"])

    status, ack = call(
        "POST",
        f"/control-room/reports/{report['report_id']}/acknowledge",
        token=control["token"],
    )
    assert status == 200 and ack["status"] == "ACKNOWLEDGED"

    # Train status is available to any logged-in role.
    status, train_state = call("GET", "/train/12303/status", token=copilot["token"])
    assert status == 200 and train_state["exists"] is True

    # Role denial: a passenger cannot read control room reports.
    status, passenger = call("POST", "/login", {
        "username": "passenger123", "password": "passenger123",
    })
    assert passenger["role"] == "PASSENGER"
    try:
        call("GET", "/control-room/reports", token=passenger["token"])
        raise AssertionError("passenger read control-room reports")
    except urllib.error.HTTPError as err:
        assert err.code == 403

    print("PASS live endpoints (login, report, list, ack, status, denial)")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    test_auth()
    test_report_store()
    test_validation_errors()
    test_priorities()
    test_route_index()

    try:
        test_live_endpoints()
    except (urllib.error.URLError, OSError):
        print("SKIP live endpoints (FastAPI not running on :8000)")
    except Exception as error:
        print(f"FAIL live endpoints: {error}")
        raise

    print("ALL STAGE 17 TESTS PASSED")