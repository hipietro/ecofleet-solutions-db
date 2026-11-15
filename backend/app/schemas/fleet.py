# File overview
# Purpose: Describe public vehicle and charging-station payloads returned by the API.
# Responsibilities: Declare vehicle details and pricing, plus station identity, city, address
#   and optional geographic coordinates.
# Connections: api/routes/fleet uses these response models; schemas/rentals reuses VehicleResponse;
#   frontend/src/types/fleet.ts mirrors the vehicle contract.

# --- Imports and module dependencies ---
from decimal import Decimal
from pydantic import BaseModel, Field


# --- Shared vehicle contract; Decimal prices serialize as strings and battery data may be missing. ---
class VehicleResponse(BaseModel):
    serialeveicolo: int
    marca:str
    modello:str
    targa:str | None=None
    statooperativo: str
    kmtotali: int
    costoorario: Decimal = Field(..., description="Hourly rate in EUR")
    livello_batteria: int | None = None


# --- Vehicle detail contract inheriting the same fields used by the public list. ---
class VehicleDetailResponse(VehicleResponse):
    #made for future, so we can add more specific fields later (ex. battery levels, hub location...)
    pass


#--- station contract: preserve unknown details and coordinates as null
class ChargingStationResponse(BaseModel):
    codicehub: int
    numerostazione: int
    citta: str
    nome: str | None = None
    indirizzo: str | None = None
    latitudine: float | None = None
    longitudine: float | None = None