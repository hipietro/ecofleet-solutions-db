from fastapi import FastAPI
from backend.app.api.routes import system, fleet, auth, rentals, corporate, backoffice
from backend.app.middleware.cors import configure_cors


app= FastAPI(
    title="Eco-Fleet Solutions API",
    description="Backend REST per la gestione della flotta aziendale e dei noleggi",
    version = "1.0.0"
)

configure_cors(app)

for router in (system.router, fleet.router, auth.router, rentals.router, corporate.router, backoffice.router):
    app.include_router(router)
