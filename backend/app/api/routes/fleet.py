from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.db.connection import get_db_connection
from backend.app.schemas import fleet as schemas

router = APIRouter()


@router.get("/api/fleet/vehicles", response_model=List[schemas.VehicleResponse], tags=["Fleet"])
def list_vehicles(stato: str |None=None, marca:str|None=None):
    """retrieve vehicles from the fleet
    supports query parameters for filtering (ex. ?stato=Disponibile&marca=BMW)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #base query
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

            cur.execute(query, tuple(params))
            veicoli=cur.fetchall()
            return veicoli


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
            
            veicolo = cur.fetchone()
            
            if not veicolo:
                raise HTTPException(status_code=404, detail="Veicolo non trovato.")
            
            return veicolo
