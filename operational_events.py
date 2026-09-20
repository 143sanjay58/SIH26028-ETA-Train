#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import uuid
from datetime import datetime, timezone

# ============================================================
# SIH26028 - OPERATIONAL EVENTS (CO-PILOT DELAY REPORTS)
# ============================================================
#
# Stores co-pilot delay reports so the Control Room can see and
# acknowledge them. The store is in-memory for the prototype;
# a production deployment would persist these records.
#
# IMPORTANT INTEGRATION NOTE
# --------------------------
# Operational events are RECORDED and DISPLAYED separately from
# the validated LightGBM prediction inputs. Submitting a report
# does NOT retrain or modify the ML models and does NOT feed the
# event into the trained models. Any ETA recalculation on top of
# a report still goes through the existing Dynamic ETA Engine.

ALLOWED_REASONS = (
    "SIGNAL_ISSUE",
    "TRACK_OBSTRUCTION",
    "TECHNICAL_ISSUE",
    "OPERATIONAL_ISSUE",
    "PASSENGER_ISSUE",
    "WEATHER_ISSUE",
    "OTHER",
)

STATUS_NEW = "NEW"
STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"

MAX_MESSAGE_LENGTH = 500


def normalize_train_number(train_number):
    """Match the engine's train_number normalization exactly."""
    if train_number is None:
        return ""
    return str(train_number).strip().lstrip("0") or "0"


def priority_for_delay(current_delay_minutes):
    """Map a reported delay to an operational priority.

    The priority comes ONLY from the reported delay magnitude,
    using the same thresholds as the existing Stage 13 delay
    impact rules. It does not exaggerate severity.

    LOW      <=  5 minutes
    MODERATE <= 15 minutes
    HIGH     <= 60 minutes
    CRITICAL >  60 minutes
    """
    delay = float(current_delay_minutes)

    if delay <= 5:
        return "LOW"
    if delay <= 15:
        return "MODERATE"
    if delay <= 60:
        return "HIGH"
    return "CRITICAL"


class OperationalEventStore:
    """In-memory store + validation for co-pilot delay reports."""

    def __init__(self, train_numbers=None, route_station_map=None):
        self._train_numbers = set()
        # normalized train number -> set of station codes on that train
        self._station_map = {}

        if train_numbers:
            self.set_train_numbers(train_numbers)

        if route_station_map:
            self._station_map = dict(route_station_map)

        self._reports = {}
        self._lock = threading.Lock()

    def set_train_numbers(self, train_numbers):
        """Accept raw or normalized train numbers; store normalized."""
        normalized = set()

        for item in train_numbers or []:
            normalized.add(normalize_train_number(item))

        self._train_numbers = normalized

    def set_route_station_map(self, route_station_map):
        self._station_map = dict(route_station_map or {})

    # ========================================================
    # VALIDATION
    # ========================================================

    def _validate(
        self,
        train_number,
        current_station,
        current_delay_minutes,
        reason,
        message,
    ):
        if train_number is None or not str(train_number).strip():
            raise ValueError("Train number is required.")

        train_number = normalize_train_number(train_number)

        if train_number not in self._train_numbers:
            raise ValueError(
                f"Train {train_number} not found in Dataset 1."
            )

        if current_station is None or not str(current_station).strip():
            raise ValueError("Current station is required.")

        current_station = str(current_station).strip().upper()

        stations = self._station_map.get(train_number)

        if stations and current_station not in stations:
            raise ValueError(
                f"Station {current_station} does not belong "
                f"to train {train_number}."
            )

        if current_delay_minutes is None:
            raise ValueError("Current delay is required.")

        try:
            delay = float(current_delay_minutes)
        except (TypeError, ValueError):
            raise ValueError(
                "Current delay must be a number of minutes."
            )

        if delay < 0:
            raise ValueError("Current delay cannot be negative.")

        if reason is None or not str(reason).strip():
            raise ValueError("Delay reason is required.")

        reason = str(reason).strip().upper()

        if reason not in ALLOWED_REASONS:
            raise ValueError(
                f"Reason must be one of: {', '.join(ALLOWED_REASONS)}."
            )

        if message is None or not str(message).strip():
            raise ValueError("Message is required.")

        message = str(message).strip()

        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message must be at most {MAX_MESSAGE_LENGTH} characters."
            )

        return train_number, current_station, delay, reason, message

    # ========================================================
    # CREATE / READ / ACKNOWLEDGE
    # ========================================================

    def create_report(
        self,
        train_number,
        copilot_id,
        current_station,
        current_delay_minutes,
        reason,
        message,
    ):
        """Validate and store a new co-pilot delay report.

        Returns the report with its unique ID, server timestamp,
        computed priority and NEW status.
        """
        if copilot_id is None or not str(copilot_id).strip():
            raise ValueError("Co-pilot identifier is required.")

        (train_number,
         current_station,
         delay,
         reason,
         message) = self._validate(
            train_number,
            current_station,
            current_delay_minutes,
            reason,
            message,
        )

        report = {
            "report_id": uuid.uuid4().hex,
            "train_number": train_number,
            "copilot_id": str(copilot_id).strip(),
            "current_station": current_station,
            "current_delay_minutes": delay,
            "reason": reason,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": priority_for_delay(delay),
            "status": STATUS_NEW,
            "acknowledged_by": None,
            "acknowledged_at": None,
            # Operational events are recorded, not fed into the ML
            # engine. The trained models are never modified here.
            "ml_models_modified": False,
            "eta_recalc": "prepared_via_existing_engine",
        }

        with self._lock:
            self._reports[report["report_id"]] = report

        return dict(report)

    def get_report(self, report_id):
        """Return a single report or None."""
        with self._lock:
            report = self._reports.get(str(report_id).strip())

        return dict(report) if report else None

    def list_reports(self, status=None, limit=None):
        """Return all reports, newest first, optionally filtered."""
        with self._lock:
            reports = list(self._reports.values())

        if status:
            reports = [
                report
                for report in reports
                if report["status"] == str(status).strip().upper()
            ]

        reports.sort(
            key=lambda report: report["timestamp"],
            reverse=True,
        )

        if limit is not None:
            reports = reports[: int(limit)]

        return [dict(report) for report in reports]

    def latest_report_for_train(self, train_number):
        """Newest report (any status) for a train, or None."""
        train_number = normalize_train_number(train_number)

        reports = [
            report
            for report in self.list_reports()
            if report["train_number"] == train_number
        ]

        return reports[0] if reports else None

    def acknowledge(self, report_id, acknowledged_by):
        """Mark a report ACKNOWLEDGED.

        Raises ValueError when the report does not exist.
        """
        report_id = str(report_id).strip()

        with self._lock:
            report = self._reports.get(report_id)

            if report is None:
                raise ValueError(
                    f"Report {report_id} not found."
                )

            report["status"] = STATUS_ACKNOWLEDGED
            report["acknowledged_by"] = str(acknowledged_by).strip()
            report["acknowledged_at"] = (
                datetime.now(timezone.utc).isoformat()
            )

            return dict(report)