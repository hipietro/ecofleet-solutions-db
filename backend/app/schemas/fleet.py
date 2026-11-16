# File overview
# Purpose: Describe public vehicle, charging-station and access-point payloads returned by the API.
# Responsibilities: Declare vehicle details, station locations and access-point occupancy,
#   preserving the distinction between unknown, free and occupied points.
# Connections: api/routes/fleet uses these response models; schemas/rentals reuses VehicleResponse;
#   frontend/src/types/fleet.ts mirrors the vehicle contract.

# --- Imports and module dependencies ---
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal


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


#--- access point contract: distinguish recorded occupancy from missing information.---
class ChargingAccessPointResponse(BaseModel):
    codicehub: int
    numerostazione: int
    numeropunto: int
    tipoconnettore: str
    veicolo: int | None = None
    stato_occupazione: Literal["non_verificato", "libero", "occupato"]#literal is used to explicit the contract by making possible only those 3 values
