# File overview
# Purpose: Resolve the authenticated account for protected API endpoints.
# Responsibilities: Decode required JWT claims, validate their types and reload the account and
#   role from PostgreSQL.
# Connections: Uses core/config and db/connection; protected routes request get_current_user
#   through Depends.

# --- Imports and module dependencies ---
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from backend.app.core.config import SECRET_KEY, ALGORITHM
from backend.app.db.connection import get_db_connection

# Read bearer credentials from the request; tokenUrl points Swagger to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# --- Authenticate the bearer token and use the current database role for authorization. ---
def get_current_user(token:str=Depends(oauth2_scheme)) -> dict:
    """extract and validate current user from JWT token"""
    try:
        # Validate signature, expiry and required account claims before querying the database.
        payload= jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            options={"require": ["sub", "cf", "role", "exp"]},
        )
        email:str=payload.get("sub")
        if not all(isinstance(payload.get(key), str) and payload[key] for key in ("sub", "cf", "role")):
            raise HTTPException(status_code=401, detail="Token non valido")
        # Reload identity and role so deleted accounts or outdated token roles are not trusted.
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT codicefiscale, email, ruolo FROM Cliente WHERE codicefiscale = %s AND email = %s;",
                (payload["cf"], email),
            ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Utente non valido")
        return {"sub": user["email"], "cf": user["codicefiscale"], "role": user["ruolo"]}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token scaduto o non valido")
