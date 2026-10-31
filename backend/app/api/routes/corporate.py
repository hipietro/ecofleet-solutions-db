import psycopg.errors
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.security import get_password_hash
from backend.app.db.connection import get_db_connection
from backend.app.schemas import corporate as schemas
from backend.app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/api/auth/register/corporate", status_code=201, tags=["Auth"])
def register_corporate(data: schemas.ClienteCorporateRegister):
    """
    Register a new corporate customer (Azienda).
    Inserts data into the parent 'cliente' table and the child 'clientecorporate' table.
    """
    hashed_pw = get_password_hash(data.password)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                # 1. Insert into base table 'cliente'
                cur.execute("""
                    INSERT INTO cliente (codicefiscale, email, telefono, dataregistrazione, password_hash, ruolo, saldo_crediti)
                    VALUES (%s, %s, %s, CURRENT_DATE, %s, 'corporate', 0.00);
                """, (data.codicefiscale, data.email, data.telefono, hashed_pw))
                
                # 2. Insert into child table 'clientecorporate'
                cur.execute("""
                    INSERT INTO clientecorporate (cliente, ragionesociale, partitaiva, livellocontratto)
                    VALUES (%s, %s, %s, %s);
                """, (data.codicefiscale, data.ragionesociale, data.partitaiva, data.livellocontratto))
                
                conn.commit()
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail="Registration failed: Email, Codice Fiscale, or Partita IVA already exists."
                )
            
    return {"message": "Corporate account created successfully."}


@router.post("/api/corporate/dipendenti", status_code=201, tags=["Corporate"])
def add_dipendente(data: schemas.DipendenteCorporateCreate, current_user: dict = Depends(get_current_user)):
    """
    Add a new employee (Dipendente) to the logged-in corporate account.
    Validates that the current user has the 'corporate' role.
    """
    # Authorization check: only corporate accounts can access this endpoint
    if current_user.get("role") != "corporate":
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only corporate accounts can add employees."
        )
        
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                # current_user["cf"] holds the company's codicefiscale (from JWT token)
                cur.execute("""
                    INSERT INTO dipendentecorporate (clientecorporate, codicedipendente, nome, cognome, reparto)
                    VALUES (%s, %s, %s, %s, %s);
                """, (current_user["cf"], data.codicedipendente, data.nome, data.cognome, data.reparto))
                
                conn.commit()
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail="Employee with this code already exists for this company."
                )
                 
    return {"message": "Employee added successfully."}
