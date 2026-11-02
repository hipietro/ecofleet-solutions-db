# File overview
# Purpose: Validate incoming maintenance records.
# Responsibilities: Describe the vehicle, technician, intervention, non-negative cost and
#   permitted resulting vehicle state.
# Connections: Used by api/routes/backoffice before data is written to Manutenzione and Veicolo.

# --- Imports and module dependencies ---
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


# --- Maintenance input with validated monetary values and allowed vehicle status labels. ---
class ManutenzioneCreate(BaseModel):
    """Request schema for logging a maintenance intervention in the Backoffice."""
    veicolo: int = Field(..., description="Vehicle ID/Serial number")
    tecnico: str = Field(..., max_length=20, description="Badge number of the technician performing the intervention")
    dataoraintervento: date = Field(..., description="Date of the intervention (YYYY-MM-DD)")
    tipointervento: str = Field(..., max_length=50)
    costo: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2, description="Cost of the intervention in Euro")
    esito: str = Field(..., max_length=100)
    nuovo_stato_veicolo: Literal['Disponibile', 'In Uso', 'In Manutenzione', 'In Carica'] = Field(
        default="Disponibile", 
        description="The new operational state of the vehicle (e.g., 'Disponibile', 'In Manutenzione')"
    )
