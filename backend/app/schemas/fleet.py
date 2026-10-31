from decimal import Decimal
from pydantic import BaseModel, Field


class VehicleResponse(BaseModel):
    serialeveicolo: int
    marca:str
    modello:str
    targa:str | None=None
    statooperativo: str
    kmtotali: int
    costoorario: Decimal = Field(..., description="Hourly rate in EUR")
    livello_batteria: int | None = None


class VehicleDetailResponse(VehicleResponse):
    #made for future, so we can add more specific fields later (ex. battery levels, hub location...)
    pass
