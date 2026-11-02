# File overview
# Purpose: Handle individual accounts, login, profiles and virtual-wallet operations.
# Responsibilities: Validate request schemas, persist account data, issue access tokens and
#   update virtual credit.
# Connections: Uses schemas/auth, core/security, api/dependencies and db/connection; Login and
#   Dashboard call these routes.

# --- Imports and module dependencies ---
import psycopg.errors
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.db.connection import get_db_connection
from backend.app.schemas import auth as schemas
from backend.app.api.dependencies import get_current_user

# --- Router collected by app/main.py; decorators below attach the public API paths ---
router = APIRouter()


# --- Create the base and private-customer records atomically with an initial virtual balance. ---
@router.post("/api/auth/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user_data: schemas.UserRegister):
    """register a new customer and initialize their virtual credit wallet"""
    # Hash before persistence; both account inserts share one connection transaction.
    hashed_pass = get_password_hash(user_data.password)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Database uniqueness constraints also protect concurrent registrations.
                cur.execute("""
                    INSERT INTO Cliente (codicefiscale, email, telefono, dataregistrazione, password_hash, ruolo, saldo_crediti)
                    VALUES (%s, %s, %s, CURRENT_DATE, %s, 'customer', 50.00);
                """, (user_data.codicefiscale, user_data.email, user_data.telefono, hashed_pass))
                cur.execute("""
                    INSERT INTO ClientePrivato (cliente, nome, cognome, patente)
                    VALUES (%s, %s, %s, %s);
                """, (user_data.codicefiscale, user_data.nome, user_data.cognome, user_data.numero_patente))
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Email, codice fiscale o patente già registrati nel sistema.")
    return {"message": "Utente registrato con successo! Wallet iniziale caricato con 50.00 €"}


# --- Verify an email/password form and return a token plus the account summary. ---
@router.post("/api/auth/login", response_model=schemas.TokenResponse, tags=["Auth"])
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

            # Reject unknown accounts and invalid credentials with the same public response.
            if not user or not user["password_hash"] or not verify_password(credentials.password, user["password_hash"]):
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


# --- Read the authenticated account balance, role and actual payment-method presence. ---
@router.get("/api/auth/me", response_model=schemas.Userprofile, tags=["Auth"])
def get_user_profile(current_user: dict = Depends(get_current_user)):
    """fetch profile details for the currentlu authenticated user."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT codicefiscale, email, ruolo, saldo_crediti,
                       default_payment_method IS NOT NULL AS has_payment_method
                FROM Cliente 
                WHERE email = %s;
            """, (current_user["sub"],))
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="Utente non trovato.")

            return user


# --- Add validated positive virtual credit and return the updated balance. ---
@router.post("/api/auth/wallet/topup", tags=["Auth"])
def topup_wallet(data: schemas.WalletTopup, current_user: dict = Depends(get_current_user)):
    """Add virtual credit to the authenticated user's wallet."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE Cliente 
                SET saldo_crediti = saldo_crediti + %s 
                WHERE email = %s
                RETURNING saldo_crediti;
            """, (data.importo, current_user["sub"]))

            # Read the new balance from PostgreSQL; this operation represents virtual credit only.
            updated_row = cur.fetchone()
            conn.commit()

            if not updated_row:
                raise HTTPException(status_code=404, detail="Utente non trovato")

            return{
                "message": f"Ricarica di {data.importo} € effettuata con successo!",
                "nuovo_saldo": updated_row["saldo_crediti"]
            }


# --- Store a simulated payment-method identifier; no payment gateway is called. ---
@router.post("/api/auth/payment-method", tags=["Auth"])
def bind_payment_method(data: schemas.PaymentethodBind, current_user: dict= Depends(get_current_user)):
    """bind a payment method token (stripe/apple pay) to the user profile."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Persist a demonstration identifier; no card details or external payment request are involved.
            cur.execute("""
                UPDATE Cliente 
                SET default_payment_method = %s 
                WHERE email = %s;
            """, (data.payment_method_id, current_user["sub"]))
            conn.commit()
            
            return {"message": "Metodo di pagamento collegato con successo!"}
