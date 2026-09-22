"""
Co-pilot delay report workflow.

A train co-pilot (STATION_STAFF role) files an operational delay report. Each
report is persisted in copilot_reports, mirrored into an Alert (control-room
queue + WebSockets) and a TrainEvent (history), and optionally triggers an ETA
refresh broadcast for trains covered by the SIH26028 core.

Reports are operational awareness ONLY - they never feed the 21 ML features of
the SIH26028 pipeline (the pipeline is frozen for the prototype; these reports
are retained for future retraining).
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import get_logger
from backend.app.models.user import User
from backend.app.models.train import Train, TrainEvent
from backend.app.models.alert import Alert, AlertType, AlertSeverity
from backend.app.models.copilot_report import (
    CoPilotReport,
    CoPilotReportPriority,
    CoPilotReportReason,
    CoPilotReportStatus,
)
from backend.app.schemas.copilot_report import CoPilotReportCreate
from backend.app.realtime.websocket_manager import manager

logger = get_logger(__name__)


def _severity_for(priority: CoPilotReportPriority) -> AlertSeverity:
    return {
        CoPilotReportPriority.HIGH: AlertSeverity.CRITICAL,
        CoPilotReportPriority.MEDIUM: AlertSeverity.WARNING,
        CoPilotReportPriority.LOW: AlertSeverity.INFO,
    }[priority]


class CoPilotReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_report(
        self, user: User, data: CoPilotReportCreate
    ) -> CoPilotReport:
        train_number = data.train_number.strip()
        station_code = (data.station_code or "").strip().upper() or None

        train = await self.db.execute(
            select(Train).where(Train.train_number == train_number)
        )
        train = train.scalar_one_or_none()

        station = None
        station_id = None
        if station_code:
            from backend.app.models.station import Station

            station_result = await self.db.execute(
                select(Station).where(Station.code == station_code)
            )
            station = station_result.scalar_one_or_none()
            station_id = station.id if station else None

        report = CoPilotReport(
            train_id=train.id if train else None,
            user_id=user.id,
            station_id=station_id,
            train_number=train_number,
            station_code=station_code,
            reason=data.reason,
            priority=data.priority,
            message=data.message.strip(),
            current_delay_minutes=data.current_delay_minutes,
            status=CoPilotReportStatus.NEW,
            is_active=True,
        )
        self.db.add(report)
        await self.db.flush()

        alert = await self._mirror_to_alert(train, station_id, report)
        await self._mirror_to_event(train.id if train else None, station_id, report)

        await self.db.flush()

        report_dict = self._to_ws_dict(report, user)
        await manager.broadcast_alert(
            {
                "id": alert.id if alert else None,
                "train_id": report.train_id,
                "station_id": report.station_id,
                "alert_type": alert.alert_type if alert else AlertType.OPERATIONAL_ANOMALY,
                "severity": alert.severity if alert else _severity_for(report.priority),
                "title": f"Co-pilot delay report for train {report.train_number}",
                "message": report.message,
                "predicted_impact_minutes": report.current_delay_minutes,
                "confidence": 0.8,
                "is_active": True,
                "is_acknowledged": False,
                "created_at": report.created_at.isoformat(),
            }
        )
        await self._broadcast_report(report_dict)

        self._schedule_eta_refresh(report)

        return report

    async def _mirror_to_alert(
        self, train: Optional[Train], station_id: Optional[int], report: CoPilotReport
    ) -> Alert:
        alert = Alert(
            train_id=report.train_id,
            station_id=station_id,
            alert_type=AlertType.OPERATIONAL_ANOMALY,
            severity=_severity_for(report.priority),
            title=f"Co-pilot delay report for train {report.train_number}",
            message=f"{report.message} (Reason: {report.reason.value})",
            predicted_impact_minutes=report.current_delay_minutes or None,
            confidence=0.8,
            is_active=True,
            is_acknowledged=False,
            alert_metadata={
                "copilot_report_id": report.id,
                "reason": report.reason.value,
                "priority": report.priority.value,
                "station_code": report.station_code,
                "train_number": report.train_number,
            },
        )
        self.db.add(alert)
        return alert

    async def _mirror_to_event(
        self, train_id: Optional[int], station_id: Optional[int], report: CoPilotReport
    ) -> None:
        if train_id is None:
            return
        event = TrainEvent(
            train_id=train_id,
            station_id=station_id,
            event_type="COPILOT_DELAY_REPORT",
            description=f"[{report.reason.value}] {report.message}",
            delay_minutes=report.current_delay_minutes,
            source="COPILOT",
            event_metadata={
                "copilot_report_id": report.id,
                "priority": report.priority.value,
                "reason": report.reason.value,
            },
        )
        self.db.add(event)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def list_my_reports(self, user: User, limit: int = 50) -> List[CoPilotReport]:
        result = await self.db.execute(
            select(CoPilotReport)
            .where(CoPilotReport.user_id == user.id)
            .options(
                selectinload(CoPilotReport.reported_by),
                selectinload(CoPilotReport.acknowledged_user),
                selectinload(CoPilotReport.closed_user),
            )
            .order_by(CoPilotReport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_reports(
        self,
        status: Optional[CoPilotReportStatus] = None,
        reason: Optional[CoPilotReportReason] = None,
        priority: Optional[CoPilotReportPriority] = None,
        train_number: Optional[str] = None,
        limit: int = 50,
    ) -> List[CoPilotReport]:
        filters = []
        if status:
            filters.append(CoPilotReport.status == status)
        if reason:
            filters.append(CoPilotReport.reason == reason)
        if priority:
            filters.append(CoPilotReport.priority == priority)
        if train_number:
            filters.append(CoPilotReport.train_number == train_number.strip())

        query = select(CoPilotReport).options(
            selectinload(CoPilotReport.reported_by),
            selectinload(CoPilotReport.acknowledged_user),
            selectinload(CoPilotReport.closed_user),
        )
        if filters:
            query = query.where(and_(*filters))
        query = query.order_by(CoPilotReport.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_with_reporters(self, report_id: int) -> Optional[CoPilotReport]:
        result = await self.db.execute(
            select(CoPilotReport)
            .where(CoPilotReport.id == report_id)
            .options(
                selectinload(CoPilotReport.reported_by),
                selectinload(CoPilotReport.acknowledged_user),
                selectinload(CoPilotReport.closed_user),
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    async def acknowledge_report(self, report_id: int, user: User) -> Optional[CoPilotReport]:
        report = await self._get_with_reporters(report_id)
        if report is None:
            return None
        now = datetime.now(timezone.utc)
        if report.status == CoPilotReportStatus.NEW:
            report.status = CoPilotReportStatus.ACKNOWLEDGED
            report.acknowledged_by = user.id
            report.acknowledged_at = now
            report.updated_at = now
            await self.db.flush()
            await self._broadcast_report(self._to_ws_dict(report, None))
        return report

    async def close_report(self, report_id: int, user: User) -> Optional[CoPilotReport]:
        report = await self._get_with_reporters(report_id)
        if report is None:
            return None
        now = datetime.now(timezone.utc)
        report.status = CoPilotReportStatus.CLOSED
        report.is_active = False
        report.closed_by = user.id
        report.closed_at = now
        report.updated_at = now
        await self.db.flush()
        await self._resolve_linked_alert(report.id)
        await self._broadcast_report(self._to_ws_dict(report, None))
        return report

    async def _resolve_linked_alert(self, report_id: int) -> None:
        result = await self.db.execute(
            select(Alert).where(Alert.alert_metadata["copilot_report_id"].as_integer() == report_id)
        )
        for alert in result.scalars().all():
            alert.is_active = False
            alert.resolved_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # WS + ETA refresh
    # ------------------------------------------------------------------

    async def _broadcast_report(self, report_dict: dict) -> None:
        await manager.broadcast_to_control_room(
            {
                "type": "copilot_report",
                "data": report_dict,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _to_ws_dict(self, report: CoPilotReport, reporter: Optional[User]) -> dict:
        return {
            "id": report.id,
            "train_id": report.train_id,
            "train_number": report.train_number,
            "station_code": report.station_code,
            "user_id": report.user_id,
            "reporter_call_sign": reporter.full_name if reporter else None,
            "reason": report.reason.value,
            "priority": report.priority.value,
            "message": report.message,
            "current_delay_minutes": report.current_delay_minutes,
            "status": report.status.value,
            "is_active": report.is_active,
            "created_at": report.created_at.isoformat(),
        }

    def _schedule_eta_refresh(self, report: CoPilotReport) -> None:
        """Best-effort background ETA refresh broadcast for covered trains."""
        if report.train_id is None:
            return

        async def _refresh():
            from backend.app.database.session import AsyncSessionLocal
            from backend.app.sih_eta.service import SIHETAService, SIHETANotCovered

            async with AsyncSessionLocal() as db:
                try:
                    result = await SIHETAService(db).predict_eta(report.train_number)
                    await manager.broadcast_eta_update(
                        report.train_id,
                        {
                            "predicted_arrival_delay_minutes": result["predicted_arrival_delay_minutes"],
                            "predicted_arrival_time": result["predicted_arrival_time"],
                            "predicted_remaining_minutes": result["predicted_remaining_minutes"],
                            "confidence_level": result.get("confidence_level"),
                            "upcoming_station_count": result["upcoming_station_count"],
                            "data_source": "SIH_ETA_CORE",
                        },
                    )
                except SIHETANotCovered:
                    pass
                except Exception as e:  # noqa: BLE001 - background task must never raise
                    logger.warning("SIH ETA refresh failed after co-pilot report", error=str(e))

        try:
            asyncio.create_task(_refresh())
        except RuntimeError:
            logger.warning("No running event loop; SIH ETA refresh skipped")