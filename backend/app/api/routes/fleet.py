# File overview
# Purpose: Expose public vehicle, charging-station and access-point endpoints.
# Responsibilities: Filter vehicles, retrieve rates, list station locations and describe
#   recorded point occupancy without treating unknown points as free.
# Connections: Uses schemas/fleet and db/connection; the React Fleet page consumes the
#   available-vehicle list and VehicleDetails consumes the individual vehicle response. Station
#   locations come from migration 002; migration 003 supplies recorded access-point occupancy.

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


#stations listing: combine each station's location with its hub's city---
@router.get(
    "/api/fleet/stations",
    response_model=List[schemas.ChargingStationResponse],
    tags=["Fleet"],
)
def list_stations():
    """return charging stations ordered by their composite identifier."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #the city belongs to the hub, but the station coordinates and address belong to the stations table
            cur.execute("""
                SELECT
                    s.codicehub,
                    s.numerostazione,
                    h.citta,
                    s.nome,
                    s.indirizzo,
                    s.latitudine,
                    s.longitudine
                FROM StazioneRicarica AS s
                JOIN HubLogistico AS h
                    ON h.codicehub = s.codicehub
                ORDER BY s.codicehub, s.numerostazione;
            """)

            return cur.fetchall()

#access points: list the recorded occupancy of one station's slots.---
@router.get(
    "/api/fleet/stations/{codicehub}/{numerostazione}/access-points",
    response_model=List[schemas.ChargingAccessPointResponse],
    tags=["Fleet"],
)
def list_access_points(codicehub: int, numerostazione: int):
    """return a station's access points, or reject an unknown station."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #check the station separately so a missing station returns HTTP 404.
            cur.execute(
                """
                SELECT 1 FROM StazioneRicarica
                WHERE codicehub = %s AND numerostazione = %s;
                """,
                (codicehub, numerostazione),
            )

            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Stazione non trovata.")

            #derive occupancy without interpreting unverified points as free.
            cur.execute(
                """
                SELECT
                    codicehub,
                    numerostazione,
                    numeropunto,
                    tipoconnettore,
                    veicolo,
                    CASE
                        WHEN NOT occupazione_verificata THEN 'non_verificato'
                        WHEN veicolo IS NULL THEN 'libero'
                        ELSE 'occupato'
                    END AS stato_occupazione
                FROM PuntoAccesso
                WHERE codicehub = %s AND numerostazione = %s
                ORDER BY numeropunto;
                """,
                (codicehub, numerostazione),
            )

            return cur.fetchall()
