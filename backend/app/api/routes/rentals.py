# File overview
# Purpose: Manage rental start, completion and the authenticated rental history.
# Responsibilities: Coordinate row locks, eligibility checks and atomic wallet, vehicle and
#   rental changes.
# Connections: Uses schemas/rentals and api/dependencies; PostgreSQL triggers own pricing,
#   mileage and receipt generation; Dashboard reads history.

# --- Imports and module dependencies ---
from decimal import Decimal
from typing import List
import psycopg.errors
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.db.connection import get_db_connection
from backend.app.schemas import rentals as schemas
from backend.app.api.dependencies import get_current_user

# --- Router collected by app/main.py; decorators below attach the public API paths ---
router = APIRouter()


# --- Lock the customer and vehicle, check eligibility and create one active rental. ---
@router.post("/api/rentals/start", response_model=schemas.RentalStartResponse, tags=["Rentals"])
def start_rental(request: schemas.RentalStartRequest, current_user: dict = Depends(get_current_user)):
    """
    Start a new vehicle rental.
    Enforces rules: single active rental per user, sufficient credit balance, and vehicle availability.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Serialize requests for the same customer before checking active rentals.
            cur.execute("SELECT saldo_crediti FROM Cliente WHERE codicefiscale = %s FOR UPDATE;", (current_user["cf"],))
            cliente = cur.fetchone()
            if not cliente:
                raise HTTPException(status_code=404, detail="Utente non trovato.")
            # 1. Business Rule: Check if user already has an ongoing active rental
            cur.execute("""
                SELECT codicenoleggio 
                FROM Noleggio 
                WHERE cliente = %s AND dataorafine IS NULL;
            """, (current_user["cf"],))
            active_rental = cur.fetchone()
            if active_rental:
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossibile avviare un nuovo noleggio: hai già una corsa attiva (Noleggio #{active_rental['codicenoleggio']})."
                )

            # 2. Business Rule: Check minimum required credit balance (e.g. 5.00 EUR)
            if cliente["saldo_crediti"] < Decimal("5.00"):
                raise HTTPException(
                    status_code=400, 
                    detail="Credito insufficiente per avviare il noleggio. Saldo minimo richiesto: 5.00 €."
                )

            # 3. Business Rule: Check vehicle existence and availability
            cur.execute("SELECT statooperativo FROM Veicolo WHERE serialeveicolo = %s FOR UPDATE;", (request.veicolo,))
            veicolo = cur.fetchone()
            if not veicolo:
                raise HTTPException(status_code=404, detail="Veicolo non trovato.")
            
            if veicolo["statooperativo"] != 'Disponibile':
                raise HTTPException(
                    status_code=400, 
                    detail=f"Il veicolo non può essere noleggiato. Stato attuale: {veicolo['statooperativo']}."
                )

            # Require a recorded battery level of at least 15 percent before the rental can start.
            cur.execute("SELECT percentualebatteria FROM Batteria WHERE veicolo = %s;", (request.veicolo,))
            batteria = cur.fetchone()
            if not batteria or batteria["percentualebatteria"] < 15:
                raise HTTPException(status_code=400, detail="Batteria insufficiente o non disponibile: richiesto almeno il 15%.")

            # 4. Action: Lock vehicle status
            cur.execute("""
                UPDATE Veicolo 
                SET statooperativo = 'In Uso' 
                WHERE serialeveicolo = %s;
            """, (request.veicolo,))

            # 5. Action: Create active rental record
            try:
                cur.execute("""
                    INSERT INTO Noleggio (cliente, veicolo, dataorainizio, hubinizio, stazioneinizio, puntoinizio)
                    VALUES (%s, %s, CURRENT_TIMESTAMP(0), %s, %s, %s)
                    RETURNING codicenoleggio, dataorainizio;
                """, (current_user["cf"], request.veicolo, request.hubinizio, request.stazioneinizio, request.puntoinizio))
                
                nuovo_noleggio = cur.fetchone()
                conn.commit()
            except (psycopg.errors.RaiseException, psycopg.errors.IntegrityError) as e:
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossibile avviare il noleggio: {e.diag.message_primary}"
                )
            
            return {
                "codicenoleggio": nuovo_noleggio["codicenoleggio"],
                "veicolo": request.veicolo,
                "dataorainizio": nuovo_noleggio["dataorainizio"],
                "messaggio": "Noleggio avviato con successo. Buon viaggio!"
            }


# --- Lock the active rental and atomically apply database pricing, wallet debit and availability. ---
@router.post("/api/rentals/stop", response_model=schemas.RentalStopResponse, tags=["Rentals"])
def stop_rental(request: schemas.RentalStopRequest, current_user: dict = Depends(get_current_user)):
    """
    terminates an active rental, calculates the cost based on minutes elapsed,
    charges the value on the credit and updates the status of the vehicle.
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Use the same lock order as start_rental and prevent duplicate charges.
            cur.execute("SELECT codicefiscale FROM Cliente WHERE codicefiscale = %s FOR UPDATE;", (current_user["cf"],))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Utente non trovato.")
            cur.execute("""
                SELECT codicenoleggio, veicolo
                FROM Noleggio
                WHERE codicenoleggio = %s AND cliente = %s AND dataorafine IS NULL
                FOR UPDATE;
            """, (request.codicenoleggio, current_user["cf"]))

            noleggio = cur.fetchone()

            if not noleggio:
                raise HTTPException(
                    status_code=404,
                    detail= " Noleggio attivo non trovato o non appartenente all'utente."
                )
            
            # The database trigger calculates the price and updates mileage once.
            try:
                cur.execute("""
                    UPDATE Noleggio
                    SET dataorafine = GREATEST(date_trunc('second', clock_timestamp())::timestamp,
                                              dataorainizio + INTERVAL '1 second'),
                        kmpercorsi = %s,
                        hubfine = %s,
                        stazionefine = %s,
                        puntofine = %s
                    WHERE codicenoleggio = %s AND dataorafine IS NULL
                    RETURNING costototale,
                              GREATEST(1, CEIL(EXTRACT(EPOCH FROM (dataorafine - dataorainizio)) / 60))::int AS durata_minuti;
                """, (
                    request.km_percorsi, 
                    request.hubfine, 
                    request.stazionefine, 
                    request.puntofine, 
                    request.codicenoleggio
                ))
                chiusura = cur.fetchone()
            except (psycopg.errors.RaiseException, psycopg.errors.IntegrityError) as e:
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossibile terminare il noleggio: {e.diag.message_primary}"
                )

            # Use the exact trigger-produced total for the wallet debit and HTTP response.
            costo_totale = chiusura["costototale"]
            minuti = chiusura["durata_minuti"]
            cur.execute("""
                UPDATE Cliente SET saldo_crediti = saldo_crediti - %s
                WHERE codicefiscale = %s AND saldo_crediti >= %s
                RETURNING saldo_crediti;
            """, (costo_totale, current_user["cf"], costo_totale))
            cliente_aggiornato = cur.fetchone()
            # Raising here rolls back the preceding rental, mileage and receipt changes as one unit.
            if not cliente_aggiornato:
                raise HTTPException(status_code=400, detail="Credito insufficiente per terminare il noleggio. Ricarica il wallet e riprova.")

            # Mileage and receipt generation belong to the database triggers.
            cur.execute("""
                UPDATE Veicolo 
                SET statooperativo = 'Disponibile'
                WHERE serialeveicolo = %s;
            """, (noleggio["veicolo"],))

            # Commit the rental, receipt, wallet and vehicle updates together.
            conn.commit()

            return {
                "codicenoleggio": request.codicenoleggio,
                "durata_minuti": minuti,
                "costo_totale": costo_totale,
                "saldo_rimanente": cliente_aggiornato["saldo_crediti"],
                "messaggio": f"Noleggio terminato con successo! Addebitati {costo_totale} € per {minuti} min., sblocco e sconto corporate inclusi se applicabile."
            }


# --- Return only the authenticated customer history with nested vehicle and battery details. ---
@router.get("/api/rentals/me", response_model=List[schemas.RentalResponse], status_code=status.HTTP_200_OK)
def get_my_rentals(current_user: dict = Depends(get_current_user)):
    """Return the authenticated customer's rentals and vehicle details."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Build the nested vehicle shape expected by RentalResponse and the React Dashboard.
            cur.execute("""
                SELECT n.codicenoleggio, n.veicolo, n.dataorainizio, n.dataorafine,
                       n.costototale AS costo_totale,
                       CASE WHEN n.dataorafine IS NULL THEN 'attivo' ELSE 'completato' END AS stato,
                       jsonb_build_object(
                           'serialeveicolo', v.serialeveicolo, 'marca', v.marca,
                           'modello', v.modello, 'targa', v.targa,
                           'statooperativo', v.statooperativo, 'kmtotali', v.kmtotali,
                           'costoorario', get_costo_orario_veicolo(v.serialeveicolo),
                           'livello_batteria', b.percentualebatteria
                       ) AS veicolo_dettagli
                FROM Noleggio n
                JOIN Veicolo v ON v.serialeveicolo = n.veicolo
                LEFT JOIN Batteria b ON b.veicolo = v.serialeveicolo
                WHERE n.cliente = %s
                ORDER BY n.dataorainizio DESC, n.codicenoleggio DESC;
            """, (current_user["cf"],))
            return cur.fetchall()
