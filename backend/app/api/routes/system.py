# File overview
# Purpose: Expose a lightweight service-health endpoint.
# Responsibilities: Return the API status and service name without reading the database.
# Connections: Registered by app/main.py and used by development tools and integration-test
#   startup checks.

# --- Imports and module dependencies ---
from fastapi import APIRouter

# --- Router collected by app/main.py; decorators below attach the public API paths ---
router = APIRouter()


# --- Return a simple process-health response without querying PostgreSQL. ---
@router.get("/health", tags=["System"])
def health_check():
    '''service state check of endpoint'''
    return {"status": "ok", "service": "Eco-Fleet API"}
