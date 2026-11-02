# File overview
# Purpose: Open psycopg connections with dictionary-shaped result rows.
# Responsibilities: Apply shared connection settings and propagate connection failures to the
#   caller.
# Connections: Reads core/config; routes and authentication dependencies manage transactions
#   with this factory.

# --- Imports and module dependencies ---
import psycopg
from psycopg.rows import dict_row
from backend.app.core.config import get_database_settings


# --- Create a dictionary-row connection whose caller controls its transaction lifetime. ---
def get_db_connection():
    '''creates and returns a connection to the db'''
    try: 
        # Dictionary rows let route code access SQL columns by name and return JSON-compatible mappings.
        connection= psycopg.connect(
            **get_database_settings(),
            row_factory=dict_row
        )
        return connection
    except Exception as error:
        print(f"Errore di connessione al databse: {error}")
        raise error
    '''if the db is off or credentials are wrong, we intercept the error to avoid the application silently failing'''
