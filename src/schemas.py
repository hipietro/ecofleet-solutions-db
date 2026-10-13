from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal

#request schema for registering a new customer
class UserRegister(BaseModel):
    codicefiscale: str = Field(..., min_length=11, max_length=16, description="Fiscal code")
    email: EmailStr
    telefono: str | None=None
    password: str=Field(..., min_length=6, description="Plain text password")
    nome: str = Field(..., min_length=2)
    cognome: str = Field(..., min_length=2)
    numero_patente: str = Field(..., min_length=5, max_length=15, description="Driver's License Number")


#request schema for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


#response schema returning JWT token and basic profle
class TokenResponse(BaseModel):
    access_token: str
    token_type: str= "bearer"
    email:str
    ruolo:str
    saldo_crediti: Decimal