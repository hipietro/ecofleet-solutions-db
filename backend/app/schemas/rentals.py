from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from backend.app.schemas.fleet import VehicleResponse


class RentalStartRequest(BaseModel):
    veicolo: int=Field(..., description="ID of the vehicle to rent")
    hubinizio: int = Field(..., description="Starting Hub ID")
    stazioneinizio: int = Field(..., description="Starting Station ID")
    puntoinizio: int = Field(..., description="Starting Access Point ID")


class RentalStartResponse(BaseModel):
    codicenoleggio: int
    veicolo: int
    dataorainizio: datetime
    messaggio:str


class RentalStopRequest(BaseModel):
    codicenoleggio: int =  Field(..., description="ID of the active rental to stop")
    hubfine: int = Field(..., description="Return Hub ID")
    stazionefine: int = Field(..., description="Return Station ID")
    puntofine: int = Field(..., description="Return Access Point ID")
    km_percorsi: int = Field(..., gt=0, description="Kilometers driven during this rental")


class RentalStopResponse(BaseModel):
    codicenoleggio: int
    durata_minuti: int
    costo_totale: Decimal
    saldo_rimanente: Decimal
    messaggio: str


class RentalResponse(BaseModel):
    codicenoleggio: int
    veicolo: int
    veicolo_dettagli: VehicleResponse | None = None
    dataorainizio: datetime
    dataorafine: datetime | None = None
    costo_totale: Decimal | None = None
    stato: str
