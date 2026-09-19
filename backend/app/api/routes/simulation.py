from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.simulation.engine import simulation_engine, SimulationState
from backend.app.schemas.simulation import (
    SimulationControlRequest,
    SimulationStatusResponse,
    SimulationScenario,
    WhatIfRequest,
    WhatIfResponse,
)
from backend.app.core.security import get_current_active_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.services.delay_propagation_service import DelayPropagationService

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    status = simulation_engine.get_status()
    return SimulationStatusResponse(
        is_running=status["state"] == SimulationState.RUNNING.value,
        is_paused=status["state"] == SimulationState.PAUSED.value,
        speed=status["speed"],
        scenario=SimulationScenario(status["scenario"]),
        active_trains=status["active_trains"],
        current_simulation_time=datetime.fromisoformat(status["simulation_time"]),
        last_update=datetime.now(timezone.utc),
    )


@router.post("/control")
async def control_simulation(
    request: SimulationControlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    if request.action == "start":
        await simulation_engine.start()
    elif request.action == "pause":
        await simulation_engine.pause()
    elif request.action == "resume":
        await simulation_engine.resume()
    elif request.action == "stop":
        await simulation_engine.stop()
    elif request.action == "reset":
        await simulation_engine.stop()
        await simulation_engine.start()
    elif request.action == "set_speed":
        if request.speed is None:
            raise HTTPException(status_code=400, detail="Speed required")
        await simulation_engine.set_speed(request.speed)
    elif request.action == "set_scenario":
        if request.scenario is None:
            raise HTTPException(status_code=400, detail="Scenario required")
        await simulation_engine.set_scenario(request.scenario)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    return {"status": "ok", "action": request.action}


@router.post("/what-if", response_model=WhatIfResponse)
async def what_if_simulation(
    request: WhatIfRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    from backend.app.models.train import Train, TrainPosition
    from sqlalchemy import select

    train_result = await db.execute(select(Train).where(Train.train_number == request.train_number))
    train = train_result.scalar_one_or_none()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    service = DelayPropagationService(db)
    current_delay = 0
    current_station = None

    position_result = await db.execute(
        select(TrainPosition)
        .where(TrainPosition.train_id == train.id)
        .order_by(TrainPosition.timestamp.desc())
        .limit(1)
    )
    position = position_result.scalar_one_or_none()
    if position:
        current_delay = position.delay_minutes
        current_station = position.current_station_id

    propagation = await service.propagate_delay(train.id, current_station, current_delay)

    final_delay = propagation[-1].get("final_predicted_delay", current_delay) if propagation else current_delay

    return WhatIfResponse(
        train_number=request.train_number,
        current_eta=datetime.now(timezone.utc) + timedelta(minutes=current_delay),
        simulated_eta=datetime.now(timezone.utc) + timedelta(minutes=final_delay),
        eta_difference_minutes=final_delay - current_delay,
        scenario_description=f"What-if: {request.scenario_type} with params {request.parameters}",
        section_impacts=propagation,
        generated_at=datetime.now(timezone.utc),
    )


from datetime import datetime, timezone, timedelta