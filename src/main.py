from fastapi import FastAPI, HTTPException #fastapi è la classe principale con cui definiamo il server API, i percorsi (endpoint) e la documentazione OpenAPI/Swagger automatica
from src.database import get_db_connection #import the main connection class

app= FastAPI(
    title="Eco-Fleet Solutions API",
    description="Backend REST per la gestione della flotta aziendale e dei noleggi",
    version = "1.0.0"
)

@app.get("/health", tags=["System"])
def health_check():
    '''service state check of endpoint'''
    return {"status": "ok", "service": "Eco-Fleet API"}

@app.get("/api/veicoli", tags=["Veicoli"])
def get_veicoli():
    '''returns the list of vehicles in the fleet'''
    try:
        with get_db_connection() as conn: #using with to make sure that the cursor and the connection get closed as soon as the request ends, to avoid memory loss or connection leaks
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT serialeveicolo, marca, modello, targa, statooperativo, kmtotali
                    FROM Veicolo
                    ORDER BY serialeveicolo ASC
                """)
                veicoli = cur.fetchall()
                return {"count": len(veicoli), "data": veicoli}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Errore durante il recupero dei veicoli dal database."
        )