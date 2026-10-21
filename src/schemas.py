from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
from datetime import datetime

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


#request schema for binding a payment method (ex. stripe / apple pay token)
class PaymentethodBind(BaseModel):
    payment_method_id: str = Field(..., min_length=5, description="Stripe/Payment gateway method ID")


#response schema for user profile
class Userprofile(BaseModel):
    codicefiscale: str
    email: str
    ruolo: str
    saldo_crediti: Decimal
    has_payment_method: bool = Field(default=False, description="True if user has bound a valid payment method")


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


#request schema for starting a rental
class RentalStartRequest(BaseModel):
    veicolo: int=Field(..., description="ID of the vehicle to rent")
    hubinizio: int = Field(..., description="Starting Hub ID")
    stazioneinizio: int = Field(..., description="Starting Station ID")
    puntoinizio: int = Field(..., description="Starting Access Point ID")


#response schema for a succesfullu started rental
class RentalStartResponse(BaseModel):
    codicenoleggio: int
    veicolo: int
    dataorainizio: datetime
    messaggio:str


#request schema for stopping an active rental
class RentalStopRequest(BaseModel):
    codicenoleggio: int =  Field(..., description="ID of the active rental to stop")
    hubfine: int = Field(..., description="Return Hub ID")
    stazionefine: int = Field(..., description="Return Station ID")
    puntofine: int = Field(..., description="Return Access Point ID")
    km_percorsi: int = Field(..., gt=0, description="Kilometers driven during this rental")


#response scheam for a successfully closed rental
class RentalStopResponse(BaseModel):
    codicenoleggio: int
    durata_minuti: int
    costo_totale: Decimal
    saldo_rimanente: Decimal
    messaggio: str


#response schema for fleet discovery vehicle list items
class VehicleResponse(BaseModel):
    serialeveicolo: int
    marca: str
    modello: str
    targa: str | None = None
    statooperativo: str
    kmtotali: int | Decimal
    costoorario: Decimal = Field(..., description="Hourly rate in EUR")


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
    livellocontratto: str = Field(..., max_length=30, description="E.g., 'Base', 'Premium', 'Flat'")


class DipendenteCorporateCreate(BaseModel):
    """
    request schema for creating a new corporate employee
    the 'clientecorporate' FK is omitted here as it will be securely inferred from the current from the user's JWT token
    """
    codicedipendente:str=Field(..., max_length=30)
    nome:str=Field(...,max_length=50)
    cognome:str=Field(...,max_length=50)
    reparto:str=Field(...,max_length=50)
