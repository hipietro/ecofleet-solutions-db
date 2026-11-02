# File overview
# Purpose: Define corporate-registration and employee-creation request contracts.
# Responsibilities: Validate company fields, supported contract tiers and bcrypt password
#   length.
# Connections: Used by api/routes/corporate; the owning company is supplied by authentication,
#   not employee input.

# --- Imports and module dependencies ---
from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Company registration input combining account credentials and contractual company data. ---
class ClienteCorporateRegister(BaseModel):
    """
    request schema for registering a new corporate customer (azienda/company).
    combines base user fields with corporate-specific fields.
    """
    #base fields for the parent 'cliente' table
    codicefiscale: str=Field(...,min_length=11, max_length=16, description="Tax ID or VAT number if coincident")
    email: EmailStr
    telefono: str=Field(..., max_length=20)
    password: str=Field(...,min_length=8)

    #specific fields for the child 'clientecorporate' table
    ragionesociale: str=Field(..., max_length=100)
    partitaiva:str=Field(...,max_length=20)
    livellocontratto: str = Field(..., max_length=30, description="Base, Silver, Gold or Premium")

    # --- Normalize supported contract tiers to the labels recognized by PostgreSQL pricing. ---
    @field_validator('livellocontratto')
    @classmethod
    def validate_contract_level(cls, value: str) -> str:
        levels = {'base': 'Base', 'silver': 'Silver', 'gold': 'Gold', 'premium': 'Premium'}
        if value.strip().lower() not in levels:
            raise ValueError('Livello contratto non valido: usare Base, Silver, Gold o Premium.')
        return levels[value.strip().lower()]

    # --- Enforce bcrypt limits using UTF-8 bytes rather than the number of characters. ---
    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode('utf-8')) > 72:
            raise ValueError('La password non può superare 72 byte UTF-8.')
        return value


# --- Employee input; the owning company is inferred from the authenticated account. ---
class DipendenteCorporateCreate(BaseModel):
    """
    request schema for creating a new corporate employee
    the 'clientecorporate' FK is omitted here as it will be securely inferred from the current from the user's JWT token
    """
    codicedipendente:str=Field(..., max_length=30)
    nome:str=Field(...,max_length=50)
    cognome:str=Field(...,max_length=50)
    reparto:str=Field(...,max_length=50)
