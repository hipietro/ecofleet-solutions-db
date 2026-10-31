from pydantic import BaseModel, EmailStr, Field, field_validator


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

    @field_validator('livellocontratto')
    @classmethod
    def validate_contract_level(cls, value: str) -> str:
        levels = {'base': 'Base', 'silver': 'Silver', 'gold': 'Gold', 'premium': 'Premium'}
        if value.strip().lower() not in levels:
            raise ValueError('Livello contratto non valido: usare Base, Silver, Gold o Premium.')
        return levels[value.strip().lower()]

    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode('utf-8')) > 72:
            raise ValueError('La password non può superare 72 byte UTF-8.')
        return value


class DipendenteCorporateCreate(BaseModel):
    """
    request schema for creating a new corporate employee
    the 'clientecorporate' FK is omitted here as it will be securely inferred from the current from the user's JWT token
    """
    codicedipendente:str=Field(..., max_length=30)
    nome:str=Field(...,max_length=50)
    cognome:str=Field(...,max_length=50)
    reparto:str=Field(...,max_length=50)
