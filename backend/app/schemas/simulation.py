from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class SimulationScenario(str, Enum):
    NORMAL = "NORMAL"
    CONGESTION = "CONGESTION"
    SIGNAL_DELAY = "SIGNAL_DELAY"
    EXTENDED_HALT = "EXTENDED_HALT"
    SPEED_RESTRICTION = "SPEED_RESTRICTION"
    HEAVY_RAIN = "HEAVY_RAIN"
    LOW_VISIBILITY = "LOW_VISIBILITY"
    PRECEDING_TRAIN_DELAY = "PRECEDING_TRAIN_DELAY"
    UNSCHEDULED_STOP = "UNSCHEDULED_STOP"
    CASCADING_DELAY = "CASCADING_DELAY"
    RECOVERY = "RECOVERY"


class SimulationControlRequest(BaseModel):
    action: str = Field(..., pattern="^(start|pause|resume|stop|reset|set_speed|set_scenario)$")
    speed: Optional[float] = Field(None, ge=0.1, le=10.0)
    scenario: Optional[SimulationScenario] = None


class SimulationStatusResponse(BaseModel):
    is_running: bool
    is_paused: bool
    speed: float
    scenario: SimulationScenario
    active_trains: int
    current_simulation_time: datetime
    last_update: datetime


class WhatIfRequest(BaseModel):
    train_number: str
    scenario_type: str = Field(..., description="Type of what-if scenario")
    parameters: dict = Field(..., description="Scenario parameters")
    simulation_duration_minutes: int = Field(default=60, ge=1, le=480)


class WhatIfResponse(BaseModel):
    train_number: str
    current_eta: datetime
    simulated_eta: datetime
    eta_difference_minutes: float
    scenario_description: str
    section_impacts: List[dict] = []
    generated_at: datetime