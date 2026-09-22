from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.app.database.session import get_db
from backend.app.services.eta_service import ETAService
from backend.app.schemas.prediction import (
    ETARequest,
    ETAResponse,
    PredictionResponse,
    SIHETAResponse,
)
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/eta/sih/{train_number}", response_model=SIHETAResponse)
async def get_sih_eta(
    train_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from backend.app.sih_eta.service import SIHETANotCovered, SIHETAService

    service = SIHETAService(db)
    try:
        result = await service.predict_eta(train_number)
        return SIHETAResponse(**result)
    except SIHETANotCovered as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SIH prediction failed: {str(e)}")


@router.post("/eta", response_model=ETAResponse)
async def predict_eta(
    request: ETARequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ETAService(db)
    try:
        result = await service.predict_eta(
            request.train_number,
            include_explanations=request.include_explanations,
            include_uncertainty=request.include_uncertainty,
        )
        return ETAResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/eta/{train_number}", response_model=ETAResponse)
async def get_eta(
    train_number: str,
    include_explanations: bool = Query(True),
    include_uncertainty: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ETAService(db)
    try:
        result = await service.predict_eta(
            train_number,
            include_explanations=include_explanations,
            include_uncertainty=include_uncertainty,
        )
        return ETAResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/trains/{train_id}", response_model=list[PredictionResponse])
async def get_train_predictions(
    train_id: int,
    station_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from sqlalchemy import select, desc, and_
    from sqlalchemy.orm import selectinload
    from backend.app.models.prediction import Prediction

    query = select(Prediction).options(selectinload(Prediction.explanations)).where(Prediction.train_id == train_id)
    if station_id:
        query = query.where(Prediction.station_id == station_id)
    query = query.order_by(desc(Prediction.prediction_time)).limit(limit)

    result = await db.execute(query)
    predictions = result.scalars().all()

    return [PredictionResponse.model_validate(p) for p in predictions]


@router.get("/current/{train_number}", response_model=ETAResponse)
async def get_current_eta(
    train_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ETAService(db)
    try:
        result = await service.predict_eta(train_number, include_explanations=True, include_uncertainty=True)
        return ETAResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")