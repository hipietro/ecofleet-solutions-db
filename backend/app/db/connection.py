import psycopg
from psycopg.rows import dict_row
from backend.app.core.config import get_database_settings


def get_db_connection():
    '''creates and returns a connection to the db'''
    try: 
        connection= psycopg.connect(
            **get_database_settings(),
            row_factory=dict_row
        )
        return connection
    except Exception as error:
        print(f"Errore di connessione al databse: {error}")
        raise error
    '''if the db is off or credentials are wrong, we intercept the error to avoid the application silently failing'''
