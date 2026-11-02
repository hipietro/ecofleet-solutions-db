# File overview
# Purpose: Assemble the EcoFleet ASGI application exposed to Uvicorn.
# Responsibilities: Create FastAPI metadata, install the shared CORS policy and register each
#   domain router.
# Connections: Imports api/routes and middleware/cors; the frontend and integration tests call
#   the resulting app.

# --- Imports and module dependencies ---
from fastapi import FastAPI
from backend.app.api.routes import system, fleet, auth, rentals, corporate, backoffice
from backend.app.middleware.cors import configure_cors


# Application metadata exposed in Swagger UI and OpenAPI.
app= FastAPI(
    title="Eco-Fleet Solutions API",
    description="Backend REST per la gestione della flotta aziendale e dei noleggi",
    version = "1.0.0"
)

# Apply the cross-origin policy before serving browser requests.
configure_cors(app)

# Register each domain router while keeping the existing endpoint paths.
for router in (system.router, fleet.router, auth.router, rentals.router, corporate.router, backoffice.router):
    app.include_router(router)
