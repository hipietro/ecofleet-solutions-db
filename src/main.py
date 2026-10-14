from fastapi import FastAPI, HTTPException, status, Depends #fastapi è la classe principale con cui definiamo il server API, i percorsi (endpoint) e la documentazione OpenAPI/Swagger automatica
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from src.database import get_db_connection #import the main connection class
from src.schemas import UserRegister, UserLogin, TokenResponse, WalletTopup, Userprofile
from src.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM

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

@app.get("/api/veicoli", tags=["Veicoli"])
def get_veicoli():
    '''returns the list of vehicles in the fleet'''
    try:
        with get_db_connection() as conn: #using with to make sure that the cursor and the connection get closed as soon as the request ends, to avoid memory loss or connection leaks
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT serialeveicolo, marca, modello, targa, statooperativo, kmtotali
                    FROM Veicolo
                    ORDER BY serialeveicolo ASC
                """)
                veicoli = cur.fetchall()
                return {"count": len(veicoli), "data": veicoli}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Errore durante il recupero dei veicoli dal database."
        )

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
            
