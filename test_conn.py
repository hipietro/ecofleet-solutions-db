from src.database import get_db_connection

try:
    conn = get_db_connection()
    print(" Connessione al database Eco-Fleet riuscita!")
    conn.close()
except Exception as e:
    print(" Connessione fallita.")