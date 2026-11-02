# File overview
# Purpose: Provide the shared environment settings used by the backend.
# Responsibilities: Locate the repository .env file, preserve environment overrides and expose
#   DB, JWT and CORS settings.
# Connections: Consumed by db/connection, core/security, api/dependencies and middleware/cors.

"""Shared environment loading and application configuration."""
# --- Imports and module dependencies ---
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env relative to the repository rather than the current shell directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / '.env')

# Shared token and browser-origin settings consumed by security and middleware.
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60
CORS_ORIGINS = ['http://localhost:5173']


# --- Build connection keyword arguments while retaining per-process environment overrides. ---
def get_database_settings():
    """Read connection settings while preserving environment overrides."""
    # Connection values are read when requested, including the test server database override.
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'dbname': os.getenv('DB_NAME', 'ecofleet'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
    }
