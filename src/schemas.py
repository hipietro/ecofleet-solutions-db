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


#request schema for topping up virtual credit wallet
class WalletTopup(BaseModel):
    importo: Decimal = Field(..., gt=0, max_digits=6, decimal_places=2, description="amount to add to a wallet")


#response schema for user profile
class Userprofile(BaseModel):
    codicefiscale: str
    email: str
    ruolo: str
    saldo_crediti: Decimal


#response schema for fleet discovery (list of vehicles)
class VehicleResponse(BaseModel):
    serialeveicolo: int
    marca:str
    modello:str
    targa:str | None=None
    statooperativo: str
    kmtotali: int


#response schema for a single vehicle detail
class VehicleDetailResponse(VehicleResponse):
    #made for future, so we can add more specific fields later (ex. battery levels, hub location...)
    pass