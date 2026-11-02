# File overview
# Purpose: Register the browser cross-origin policy for the API.
# Responsibilities: Allow the configured frontend origin, credentials, HTTP methods and request
#   headers.
# Connections: Reads core/config and is called by app/main.py; it does not authenticate
#   individual requests.

# --- Imports and module dependencies ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import CORS_ORIGINS


# --- Install the shared origin policy on the FastAPI instance supplied by main.py. ---
def configure_cors(app: FastAPI) -> None:
    """Register the existing cross-origin policy."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
