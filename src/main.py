from fastapi import FastAPI, HTTPException, status, Depends #fastapi è la classe principale con cui definiamo il server API, i percorsi (endpoint) e la documentazione OpenAPI/Swagger automatica
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from src.database import get_db_connection #import the main connection class
from src.schemas import UserRegister, UserLogin, TokenResponse, WalletTopup, Userprofile, VehicleResponse, VehicleDetailResponse, RentalStartRequest, RentalStartResponse,RentalStopRequest,RentalStopResponse
from src.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from typing import List
import psycopg.errors
from decimal import Decimal

app= FastAPI(
    title="Eco-Fleet Solutions API",
    description="Backend REST per la gestione della flotta aziendale e dei noleggi",
    version = "1.0.0"
)

oauth2_scheme= OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token:str=Depends(oauth2_scheme)) -> dict:
    """extract and validate current user from JWT token"""
    try:
        payload= jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email:str=payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token non valido")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token scaduto o non valido")

@app.get("/health", tags=["System"])
def health_check():
    '''service state check of endpoint'''
    return {"status": "ok", "service": "Eco-Fleet API"}

@app.get("/api/fleet/vehicles", response_model=List[VehicleResponse], tags=["Fleet"])
def list_vehicles(stato: str |None=None, marca:str|None=None):
    """retrieve vehicles from the fleet
    supports query parameters for filtering (ex. ?stato=Disponibile&marca=BMW)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #base query
            query="""
                SELECT serialeveicolo, marca, modello, targa, statooperativo, kmtotali, costoorario 
                FROM Veicolo 
                WHERE 1=1
            """
            params=[]

            #dynamic filtering based on query parameters
            if stato:
                query+="AND statooperativo = %s"
                params.append(stato)
            if marca:
                query+="AND marca = %s"
                params.append(marca)

            query+="ORDER BY serialeveicolo ASC;"

            cur.execute(query, tuple(params))
            veicoli=cur.fetchall()
            return veicoli


@app.get("/api/fleet/vehicles/{seriale}", response_model=VehicleDetailResponse, tags=["Fleet"])
def get_vehicle_by_id(seriale: int):
    """Retrieve detailed information for a specific vehicle by its serial number."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT serialeveicolo, marca, modello, targa, statooperativo, kmtotali, costoorario 
                FROM Veicolo 
                WHERE serialeveicolo = %s;
            """, (seriale,))
            
            veicolo = cur.fetchone()
            
            if not veicolo:
                raise HTTPException(status_code=404, detail="Veicolo non trovato.")
            
            return veicolo

        

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user_data: UserRegister):
    """register a new customer and initialize their virtual credit wallet"""
    hashed_pass = get_password_hash(user_data.password)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #check if email or fiscal code already exist
            cur.execute("SELECT email FROM Cliente WHERE email= %s OR codicefiscale = %s;", 
                        (user_data.email, user_data.codicefiscale))
            if cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Email o codice fiscale già registrati nel sistema."
                )

            #insert into base Cliente table
            cur.execute("""
                INSERT INTO Cliente (codicefiscale, email, telefono, dataregistrazione, password_hash, ruolo, saldo_crediti)
                VALUES (%s, %s, %s, CURRENT_DATE, %s, 'customer', 50.00);
            """, (user_data.codicefiscale, user_data.email, user_data.cognome, hashed_pass))

            #insert into ClientePrivato table
            cur.execute("""
                INSERT INTO ClientePrivato (cliente, nome, cognome, patente)
                VALUES (%s, %s, %s, %s);
            """, (user_data.codicefiscale, user_data.nome, user_data.cognome, user_data.numero_patente))

            conn.commit()
        return {"message": "Utente registrato con successo! Wallet iniziale caricato con 50.00 €"}

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
def login_user(credentials: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user credentials and return JWT token with profile info."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT codicefiscale, email, password_hash, ruolo, saldo_crediti 
                FROM Cliente 
                WHERE email = %s;
            """, (credentials.username,))
            user = cur.fetchone()

            if not user or not verify_password(credentials.password, user["password_hash"]):
                raise HTTPException(
                    status_code=401,
                    detail="Credenziali non valide (email o password errrate)."
                )

            #create token with user information payload
            access_token = create_access_token({
                "sub": user["email"],
                "cf": user["codicefiscale"],
                "role": user["ruolo"]
            })

            #return data matching the TokenResponse schema
            #pydantic will automatically validate and format saldo_crediti as Decimal

            return{
                "access_token": access_token,
                "token_type": "bearer",
                "email": user["email"],
                "ruolo": user["ruolo"],
                "saldo_crediti": user["saldo_crediti"]
            }


@app.get("/api/auth/me", response_model=Userprofile, tags=["Auth"])
def get_user_profile(current_user: dict = Depends(get_current_user)):
    """fetch profile details for the currentlu authenticated user."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT codicefiscale, email, ruolo, saldo_crediti 
                FROM Cliente 
                WHERE email = %s;
            """, (current_user["sub"],))
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="Utente non trovato.")

            return user


@app.post("/api/auth/wallet/topup", tags=["Auth"])
def topup_wallet(data: WalletTopup, current_user: dict = Depends(get_current_user)):
    """Add virtual credit to the authenticated user's wallet."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE Cliente 
                SET saldo_crediti = saldo_crediti + %s 
                WHERE email = %s
                RETURNING saldo_crediti;
            """, (data.importo, current_user["sub"]))

            updated_row = cur.fetchone()
            conn.commit()

            if not updated_row:
                raise HTTPException(status_code=404, detail="Utente non trovato")

            return{
                "message": f"Ricarica di {data.importo} € effettuata con successo!",
                "nuovo_saldo": updated_row["saldo_crediti"]
            }



@app.post("/api/rentals/start", response_model=RentalStartResponse, tags=["rentals"])
def start_rental(request:RentalStartRequest, current_user: dict=Depends(get_current_user)):
    """
    avvia un nuovo noleggio
    controlla la disponibilità del veicolo e il saldo minimo del cliente
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #rule 1: does the client have sufficient credit?(minimum 5.00€)
            cur.execute("SELECT saldo_crediti FROM Cliente WHERE codicefiscale =%s;", (current_user["cf"],))
            cliente=cur.fetchone()
            if cliente["saldo_crediti"]<5.00:
                raise HTTPException(
                    status_code=400,
                    detail="Credito insufficiente per avviare il noleggio. Ricarica il wallet(minimo richiesto: 5.00)."
                )

            #rule 2: does the vehicle exist and is it available?
            cur.execute("SELECT statooperativo FROM Veicolo WHERE serialeveicolo = %s;", (request.veicolo,))
            veicolo = cur.fetchone()
            if not veicolo:
                raise HTTPException(status_code=404, detail="Veicolo non trovato.")
            
            if veicolo["statooperativo"] != 'Disponibile':
                raise HTTPException(
                    status_code=400, 
                    detail=f"Il veicolo non può essere noleggiato. Stato attuale: {veicolo['statooperativo']}."
                )

            #rule 3: change the state of the vehicle
            cur.execute("""
                UPDATE Veicolo 
                SET statooperativo = 'In Uso' 
                WHERE serialeveicolo = %s;
            """, (request.veicolo,))

            #rule 4: create the rental record
            #using CURRENT_TIMESTAMP(0) to round to exact seconds
            try:
                cur.execute("""
                    INSERT INTO Noleggio (cliente, veicolo, dataorainizio, hubinizio, stazioneinizio, puntoinizio)
                    VALUES (%s, %s, CURRENT_TIMESTAMP(0), %s, %s, %s)
                    RETURNING codicenoleggio, dataorainizio;
                """, (current_user["cf"], request.veicolo, request.hubinizio, request.stazioneinizio, request.puntoinizio))

                nuovo_noleggio=cur.fetchone()

                #applies all the updates simultaneously (atomic transaction)
                conn.commit()
            except psycopg.errors.RaiseException as e:
                #intercepts the error generated by the PL/pgSQL trigger and returns a clean message instead of a generic 500 error
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossibile avviare il noleggio: {e.diag.message_primary}"
                )
            
            return{
                "codicenoleggio": nuovo_noleggio["codicenoleggio"],
                "veicolo": request.veicolo,
                "dataorainizio": nuovo_noleggio["dataorainizio"],
                "messaggio": "Noleggio avviato con successo. Buon viaggio!"
            }


@app.post("/api/rentals/stop", response_model=RentalStopResponse, tags=["rentals"])
def stop_rental(request: RentalStopRequest, current_user: dict = Depends(get_current_user)):
    """
    terminates an active rental, calculates the cost based on minutes elapsed,
    charges the value on the credit and updates the status of the vehicle.
    """

    #ixed unlock fee in EUR
    UNLOCK_FEE = Decimal("1.00")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Retrieves the user's active rental
            cur.execute("""
                SELECT n.codicenoleggio, n.veicolo, n.dataorainizio, v.costoorario
                       EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP(0) - n.dataorainizio))/60 AS minuti_trascorsi
                FROM Noleggio n
                JOIN Veicolo v ON n.veicolo = v.serialeveicolo
                WHERE n.codicenoleggio = %s AND n.cliente = %s AND n.dataorafine IS NULL;
            """, (request.codicenoleggio, current_user["cf"]))

            noleggio = cur.fetchone()

            if not noleggio:
                raise HTTPException(
                    status_code=404,
                    detail= " Noleggio attivo non trovato o non appartenente all'utente."
                )
            
            #2 calculates minutes (minimum 1 minute) and the total cost (ex. 0.25 €/min)
            minuti=max(1, int(noleggio["minuti_trascorsi"]))
            costo_al_minuto = noleggio["costoorario"]/Decimal("60.00")
            costo_corsa=Decimal(str(round(minuti*float(costo_al_minuto), 2)))
            costo_totale = UNLOCK_FEE + costo_corsa

            #3 charges the cost on the client credit
            cur.execute("""
                UPDATE Cliente 
                SET saldo_crediti = saldo_crediti - %s 
                WHERE codicefiscale = %s 
                RETURNING saldo_crediti;
            """, (costo_totale, current_user["cf"]))
            
            cliente_aggiornato = cur.fetchone()

            #4 closes the rental updating end-time, cost, km and finish point
            try:
                cur.execute("""
                    UPDATE Noleggio
                    SET dataorafine = CURRENT_TIMESTAMP(0),
                        costototale = %s,
                        kmpercorsi = %s,
                        hubfine = %s,
                        stazionefine = %s,
                        puntofine = %s
                    WHERE codicenoleggio = %s;
                """, (
                    costo_totale, 
                    request.km_percorsi, 
                    request.hubfine, 
                    request.stazionefine, 
                    request.puntofine, 
                    request.codicenoleggio
                ))
            except psycopg.errors.RaiseException as e:
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossibile terminare il noleggio: {e.diag.message_primary}"
                )

            #5 brings back the vehicle to "Disponibile" (available) and updates total km
            cur.execute("""
                UPDATE Veicolo 
                SET statooperativo = 'Disponibile',
                    kmtotali = kmtotali + %s
                WHERE serialeveicolo = %s;
            """, (request.km_percorsi, noleggio["veicolo"]))

            # Transazione atomica
            conn.commit()

            return {
                "codicenoleggio": request.codicenoleggio,
                "durata_minuti": minuti,
                "costo_totale": costo_totale,
                "saldo_rimanente": cliente_aggiornato["saldo_crediti"],
                "messaggio": f"Noleggio terminato con successo! Addebitati {costo_totale} € ({UNLOCK_FEE} € sblocco + {costo_corsa} € per {minuti} min.)"
            }
