# File overview
# Purpose: Define rental request and response contracts.
# Responsibilities: Validate start/stop inputs and describe completion totals and history with
#   nested vehicle details.
# Connections: Used by api/routes/rentals; imports schemas/fleet; Dashboard consumes the history
#   response.

# --- Imports and module dependencies ---
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from backend.app.schemas.fleet import VehicleResponse


# --- Start input: selected vehicle and the composite identity of its departure access point. ---
class RentalStartRequest(BaseModel):
    veicolo: int=Field(..., description="ID of the vehicle to rent")
    hubinizio: int = Field(..., description="Starting Hub ID")
    stazioneinizio: int = Field(..., description="Starting Station ID")
    puntoinizio: int = Field(..., description="Starting Access Point ID")


# --- Start output: created rental identifier, vehicle, timestamp and confirmation message. ---
class RentalStartResponse(BaseModel):
    codicenoleggio: int
    veicolo: int
    dataorainizio: datetime
    messaggio:str


# --- Completion input: rental, return access point and positive distance travelled. ---
class RentalStopRequest(BaseModel):
    codicenoleggio: int =  Field(..., description="ID of the active rental to stop")
    hubfine: int = Field(..., description="Return Hub ID")
    stazionefine: int = Field(..., description="Return Station ID")
    puntofine: int = Field(..., description="Return Access Point ID")
    km_percorsi: int = Field(..., gt=0, description="Kilometers driven during this rental")


# --- Completion output: database price, billable minutes, remaining balance and confirmation. ---
class RentalStopResponse(BaseModel):
    codicenoleggio: int
    durata_minuti: int
    costo_totale: Decimal
    saldo_rimanente: Decimal
    messaggio: str


# --- Personal-history output, reusing VehicleResponse for nested vehicle details. ---
class RentalResponse(BaseModel):
    codicenoleggio: int
    veicolo: int
    veicolo_dettagli: VehicleResponse | None = None
    dataorainizio: datetime
    dataorafine: datetime | None = None
    costo_totale: Decimal | None = None
    stato: str
