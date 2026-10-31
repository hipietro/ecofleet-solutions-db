import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from backend.app.core.config import SECRET_KEY, ALGORITHM
from backend.app.db.connection import get_db_connection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token:str=Depends(oauth2_scheme)) -> dict:
    """extract and validate current user from JWT token"""
    try:
        payload= jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            options={"require": ["sub", "cf", "role", "exp"]},
        )
        email:str=payload.get("sub")
        if not all(isinstance(payload.get(key), str) and payload[key] for key in ("sub", "cf", "role")):
            raise HTTPException(status_code=401, detail="Token non valido")
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
