#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pandas as pd
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from role_auth import (
    AuthService,
    ROLE_PASSENGER,
    ROLE_CONTROL_ROOM,
    ROLE_CO_PILOT,
)
from operational_events import (
    OperationalEventStore,
    normalize_train_number,
)

# ============================================================
# SIH26028 - ROLE-BASED API (PASSENGER / CONTROL ROOM / CO-PILOT)
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ROUTE_FILE = os.path.join(BASE_DIR, "ml_ready_segments_final.csv")


# ============================================================
# ROUTE INDEX (train numbers + stations) FROM THE FROZEN DATA
# ============================================================

def build_route_index():
    """Return normalized train numbers, per-train station codes and
    per-train route lengths from the frozen route dataset."""
    usecols = [
        "train_number",
        "route_order",
        "from_station",
        "to_station",
        "from_station_canonical",
        "to_station_canonical",
    ]

    df = pd.read_csv(ROUTE_FILE, usecols=usecols)

    train_norm = (
        df["train_number"]
        .astype(str)
        .str.strip()
        .str.lstrip("0")
        .replace("", "0")
    )

    train_numbers = set(train_norm.unique())
    route_lengths = (
        df.groupby(train_norm)["route_order"].max() + 1
    )

    station_map = {}

    for train, sub in df.groupby(train_norm):
        codes = set()
        codes.update(
            sub["from_station"]
            .astype(str).str.strip().str.upper()
        )
        codes.update(
            sub["to_station"]
            .astype(str).str.strip().str.upper()
        )
        codes.update(
            sub["from_station_canonical"]
            .astype(str).str.strip().str.upper()
        )
        codes.update(
            sub["to_station_canonical"]
            .astype(str).str.strip().str.upper()
        )
        station_map[train] = codes

    route_lengths = {
        str(train): int(length)
        for train, length in route_lengths.items()
    }

    return {
        "train_numbers": train_numbers,
        "route_station_map": station_map,
        "route_lengths": route_lengths,
    }


ROUTE_INDEX = build_route_index()

EVENT_STORE = OperationalEventStore(
    train_numbers=ROUTE_INDEX["train_numbers"],
    route_station_map=ROUTE_INDEX["route_station_map"],
)

AUTH = AuthService()

# Demo recorded state (prototype placeholder; no live IR feed).
DEMO_STATES = {
    "12303": {
        "current_station": "BEQ",
        "current_route_position": 3,
        "current_delay_minutes": 17.0,
        "source": "recorded_demo",
    },
}

DEMO_ROUTES = {
    "12303": ["LLH", "BEQ", "BLY", "BZL", "DKAE", "GBRA", "JOX"],
}

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class DelayReportRequest(BaseModel):
    train_number: str
    current_station: str
    current_delay_minutes: float
    reason: str
    message: str


# ============================================================
# AUTH HELPERS
# ============================================================

def _parse_token(authorization):
    """Extract the bearer token from an Authorization header."""
    if not authorization:
        return None

    parts = str(authorization).split()

    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()

    return None


def _require_role(authorization, allowed_roles):
    token = _parse_token(authorization)

    try:
        return AUTH.require_role(token, allowed_roles)
    except ValueError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )


# ============================================================
# LOGIN / LOGOUT
# ============================================================

@router.post("/login", tags=["auth"])
def login(request: LoginRequest):
    try:
        return AUTH.login(
            request.username,
            request.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
        )


@router.post("/logout", tags=["auth"])
def logout(authorization: str = Header(default=None)):
    AUTH.logout(_parse_token(authorization))
    return {"status": "success", "message": "Logged out."}


# ============================================================
# CO-PILOT DELAY REPORT
# ============================================================

@router.post("/copilot/delay-report", tags=["copilot"])
def submit_delay_report(
    request: DelayReportRequest,
    authorization: str = Header(default=None),
):
    session = _require_role(authorization, [ROLE_CO_PILOT])

    try:
        report = EVENT_STORE.create_report(
            train_number=request.train_number,
            copilot_id=session["username"],
            current_station=request.current_station,
            current_delay_minutes=request.current_delay_minutes,
            reason=request.reason,
            message=request.message,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    report["received_by_backend"] = True
    report["control_room_notified"] = True

    return report


# ============================================================
# CONTROL ROOM
# ============================================================

@router.get("/control-room/reports", tags=["control-room"])
def list_control_room_reports(
    status: str = None,
    authorization: str = Header(default=None),
):
    _require_role(authorization, [ROLE_CONTROL_ROOM])

    return {
        "status": "success",
        "reports": EVENT_STORE.list_reports(status=status),
    }


@router.post(
    "/control-room/reports/{report_id}/acknowledge",
    tags=["control-room"],
)
def acknowledge_report(
    report_id: str,
    authorization: str = Header(default=None),
):
    session = _require_role(authorization, [ROLE_CONTROL_ROOM])

    try:
        report = EVENT_STORE.acknowledge(
            report_id,
            acknowledged_by=session["username"],
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    report["control_room_acknowledged"] = True

    return report


# ============================================================
# TRAIN STATUS (all logged-in roles)
# ============================================================

@router.get("/train/{train_number}/status", tags=["train"])
def train_status(
    train_number: str,
    authorization: str = Header(default=None),
):
    _require_role(
        authorization,
        [ROLE_PASSENGER, ROLE_CONTROL_ROOM, ROLE_CO_PILOT],
    )

    normalized = normalize_train_number(train_number)

    if normalized not in ROUTE_INDEX["train_numbers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Train {train_number} not found.",
        )

    demo_state = dict(DEMO_STATES.get(normalized, {}))

    if demo_state:
        current_state = demo_state
    else:
        current_state = {
            "current_station": "UNKNOWN",
            "current_route_position": 1,
            "current_delay_minutes": 0.0,
            "source": "schedule_default",
        }

    upstream_route = DEMO_ROUTES.get(normalized, [])

    latest_report = EVENT_STORE.latest_report_for_train(normalized)

    return {
        "status": "success",
        "train_number": normalized,
        "exists": True,
        "current_state": current_state,
        "route": {
            "route_length": ROUTE_INDEX["route_lengths"].get(
                normalized, 0
            ),
            "upcoming_stations": upstream_route,
            "is_simulated_route": bool(
                normalized in DEMO_ROUTES
            ),
        },
        "latest_delay_report": latest_report,
        "eta_note": (
            "Operational events are recorded and displayed "
            "separately from the trained LightGBM inputs. "
            "The ML models are not modified by delay reports."
        ),
    }