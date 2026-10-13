import os
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from dotenv import load_dotenv

#load enviroment variables
load_dotenv()

#JWT vonfiguration settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_fallback_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

#initialize password hasher using bcrypt
password_hash_context = PasswordHash((BcryptHasher(),))

def verify_password(plain_password: str, hashed_password:str) -> bool:
    """verify a plain text password against a stored hashed password."""
    return password_hash_context.verify(plain_password, hashed_password)

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