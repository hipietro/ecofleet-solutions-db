from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from pwdlib.exceptions import UnknownHashError
from backend.app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Validate the signing key before the application starts.
if not SECRET_KEY:
    raise ValueError("FATAL ERROR: JWT_SECRET_KEY enviroment variable is missing. Application cannot start securely.")

#initialize password hasher using bcrypt
password_hash_context = PasswordHash((BcryptHasher(),))

def verify_password(plain_password: str, hashed_password:str) -> bool:
    """verify a plain text password against a stored hashed password."""
    try:
        return password_hash_context.verify(plain_password, hashed_password)
    except (ValueError, UnknownHashError):
        # Invalid legacy hashes and oversized passwords must not cause HTTP 500.
        return False

def get_password_hash(password:str) -> str:
    """hash a plain text password using bcrypt"""
    return password_hash_context.hash(password)

def create_access_token(data:dict, expires_delta:timedelta | None=None) -> str:
    """generate a signed JWT access token with an expiration timestamp"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
