# File overview
# Purpose: Describe the public vehicle payloads returned by the API.
# Responsibilities: Declare identifiers, status, mileage, individual hourly pricing and optional
#   battery information.
# Connections: Used by api/routes/fleet and schemas/rentals; mirrored by
#   frontend/src/types/fleet.ts.

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
