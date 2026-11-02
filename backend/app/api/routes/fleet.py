# File overview
# Purpose: Expose public vehicle-list and vehicle-detail endpoints.
# Responsibilities: Apply optional filters, retrieve each vehicle rate through PostgreSQL and
#   return vehicle schemas.
# Connections: Uses schemas/fleet and db/connection; the React Fleet page consumes the
#   available-vehicle list.

# --- Imports and module dependencies ---
from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.db.connection import get_db_connection
from backend.app.schemas import fleet as schemas

# --- Router collected by app/main.py; decorators below attach the public API paths ---
router = APIRouter()


# --- Build a parameterized vehicle query and apply the optional status and brand filters. ---
@router.get("/api/fleet/vehicles", response_model=List[schemas.VehicleResponse], tags=["Fleet"])
def list_vehicles(stato: str |None=None, marca:str|None=None):
    """retrieve vehicles from the fleet
    supports query parameters for filtering (ex. ?stato=Disponibile&marca=BMW)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #base query
            # Use the existing database function because hourly rates belong to vehicle subtype rows.
            query="""
                SELECT serialeveicolo, marca, modello, targa, statooperativo, kmtotali,
                       get_costo_orario_veicolo(serialeveicolo) AS costoorario
                FROM Veicolo 
                WHERE 1=1
            """
            params=[]

            #dynamic filtering based on query parameters
            if stato:
                query+=" AND statooperativo = %s "
                params.append(stato)
            if marca:
                query+=" AND marca = %s "
                params.append(marca)

            query+="ORDER BY serialeveicolo ASC;"

            # Bind filter values separately from SQL text to avoid treating user input as SQL.
            cur.execute(query, tuple(params))
            veicoli=cur.fetchall()
            return veicoli


# --- Read one vehicle and its subtype-specific hourly rate, or return HTTP 404. ---
@router.get("/api/fleet/vehicles/{seriale}", response_model=schemas.VehicleDetailResponse, tags=["Fleet"])
def get_vehicle_by_id(seriale: int):
    """Retrieve detailed information for a specific vehicle by its serial number."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT serialeveicolo, marca, modello, targa, statooperativo, kmtotali,
                       get_costo_orario_veicolo(serialeveicolo) AS costoorario
                FROM Veicolo 
                WHERE serialeveicolo = %s;
            """, (seriale,))
            
            # Distinguish an unknown vehicle from a successful detail response.
            veicolo = cur.fetchone()
            
            if not veicolo:
                raise HTTPException(status_code=404, detail="Veicolo non trovato.")
            
            return veicolo
