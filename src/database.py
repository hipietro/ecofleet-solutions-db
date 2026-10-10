import os #to read ambient variables
import psycopg #postgres driver, opens the TCP channel to the db on 5432
from psycopg.rows import dict_row # to automatically transform the tuples that postgres gives us in dictionaries, ideal to send a JSON to web interface
from dotenv import load_dotenv #to read .env file

load_dotenv()#loads the .env file

def get_db_connection():
    '''creates and returns a connection to the db'''
    try: 
        connection= psycopg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "ecofleet"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            row_factory=dict_row
        )
        return connection
    except Exception as error:
        print(f"Errore di connessione al databse: {error}")
        raise error
    '''if the db is off or credentials are wrong, we intercept the error to avoid the application silently failing'''