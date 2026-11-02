# File overview
# Purpose: Define account, authentication and virtual-wallet API contracts.
# Responsibilities: Validate registration/password limits and describe login, profile, top-up
#   and payment-method payloads.
# Connections: Imported by api/routes/auth; the frontend Login and Dashboard consume the
#   corresponding responses.

# --- Imports and module dependencies ---
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Private registration input: identity/contact details, credentials and driver information. ---
class UserRegister(BaseModel):
    codicefiscale: str = Field(..., min_length=11, max_length=16, description="Fiscal code")
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=20)
    password: str=Field(..., min_length=6, description="Plain text password")
    nome: str = Field(..., min_length=2)
    cognome: str = Field(..., min_length=2)
    numero_patente: str = Field(..., min_length=5, max_length=15, description="Driver's License Number")

    # --- Enforce bcrypt limits using UTF-8 bytes rather than the number of characters. ---
    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        # Bcrypt limits passwords by UTF-8 bytes rather than character count.
        if len(value.encode('utf-8')) > 72:
            raise ValueError('La password non può superare 72 byte UTF-8.')
        return value


# --- JSON-shaped credential model retained for reuse; the live login route consumes an OAuth2 form. ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# --- Login output: bearer token and the profile summary consumed by the frontend. ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str= "bearer"
    email:str
    ruolo:str
    saldo_crediti: Decimal


# --- Positive virtual-credit input with bounded decimal precision. ---
class WalletTopup(BaseModel):
    importo: Decimal = Field(..., gt=0, max_digits=6, decimal_places=2, description="amount to add to a wallet")


# --- Simulated payment-method input; this identifier does not authorize a real charge. ---
class PaymentethodBind(BaseModel):
    payment_method_id: str = Field(..., min_length=5, description="Stripe/Payment gateway method ID")


# --- Profile output including the balance and actual stored payment-method presence. ---
class Userprofile(BaseModel):
    codicefiscale: str
    email: str
    ruolo: str
    saldo_crediti: Decimal
    has_payment_method: bool = Field(default=False, description="True if user has bound a valid payment method")
