from fastapi import APIRouter, Depends

from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.network import NetworkRoutesResponse
from backend.app.services.network_service import get_network_routes

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/routes", response_model=NetworkRoutesResponse)
def network_routes(current_user: User = Depends(get_current_active_user)):
    network = get_network_routes()
    return NetworkRoutesResponse(stations=network.stations, edges=network.edges)