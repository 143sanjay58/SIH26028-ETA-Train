from typing import List
from pydantic import BaseModel


class NetworkStation(BaseModel):
    code: str
    name: str
    latitude: float
    longitude: float


class NetworkRoutesResponse(BaseModel):
    stations: List[NetworkStation]
    edges: List[List[str]]