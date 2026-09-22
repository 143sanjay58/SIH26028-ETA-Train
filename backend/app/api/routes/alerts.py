from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from backend.app.database.session import get_db
from backend.app.services.alert_service import AlertService
from backend.app.schemas.alert import AlertResponse, AlertType, AlertSeverity
from backend.app.core.security import get_current_active_user, require_roles
from backend.app.models.user import User, UserRole

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    train_id: Optional[int] = None,
    station_id: Optional[int] = None,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AlertService(db)
    alerts = await service.get_active_alerts(train_id, station_id, severity)

    if alert_type:
        alerts = [a for a in alerts if a.alert_type == alert_type]

    return alerts[:limit]


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STATION_STAFF, UserRole.SUPERVISOR, UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = AlertService(db)
    alert = await service.acknowledge_alert(alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERVISOR, UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = AlertService(db)
    alert = await service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.post("/train/{train_id}/generate", response_model=List[AlertResponse])
async def generate_train_alerts(
    train_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = AlertService(db)
    alerts = await service.generate_alerts_for_train(train_id)
    return [AlertResponse.model_validate(a) for a in alerts]