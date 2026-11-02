# File overview
# Purpose: Expose staff maintenance operations and manager-only fleet reports.
# Responsibilities: Check staff roles, record maintenance, calculate rental statistics and
#   generate Excel downloads.
# Connections: Uses schemas/backoffice, api/dependencies, PostgreSQL, pandas, NumPy and
#   OpenPyXL.

# --- Imports and module dependencies ---
import io
import numpy as np
import pandas as pd
import psycopg.errors
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.db.connection import get_db_connection
from backend.app.schemas import backoffice as schemas
from backend.app.api.dependencies import get_current_user

# --- Router collected by app/main.py; decorators below attach the public API paths ---
router = APIRouter()


# --- Authorize staff and commit a maintenance record with its resulting vehicle state. ---
@router.post("/api/backoffice/maintenance", status_code=201, tags=["Backoffice"])
def register_maintenance(data: schemas.ManutenzioneCreate, current_user: dict = Depends(get_current_user)):
    """
    Log a maintenance intervention and update the vehicle's operational status.
    Access restricted to users with 'manager' or 'technician' roles.
    """
    # Authorization check
    # Match the staff role names enforced by the Cliente role constraint.
    if current_user.get("role") not in ["manager", "technician"]:
        raise HTTPException(
            status_code=403, 
            detail="Accesso negato. Endpoint riservato allo staff di backoffice."
        )

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Verify vehicle existence
            cur.execute("SELECT serialeveicolo FROM Veicolo WHERE serialeveicolo = %s;", (data.veicolo,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Veicolo non trovato.")

            # 2. Verify technician existence
            cur.execute("SELECT matricola FROM Tecnico WHERE matricola = %s;", (data.tecnico,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail=f"Tecnico con matricola {data.tecnico} non trovato.")

            try:
                # 3. Insert the intervention log into the database
                cur.execute("""
                    INSERT INTO manutenzione (veicolo, tecnico, dataoraintervento, tipointervento, costo, esito)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (data.veicolo, data.tecnico, data.dataoraintervento, data.tipointervento, data.costo, data.esito))
                
                # 4. Update the vehicle's operational status
                cur.execute("""
                    UPDATE Veicolo 
                    SET statooperativo = %s 
                    WHERE serialeveicolo = %s;
                """, (data.nuovo_stato_veicolo, data.veicolo))
                
                conn.commit()
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail="Intervento già registrato per questo veicolo, tecnico e data."
                )

    return {
        "message": "Manutenzione registrata con successo.",
        "veicolo": data.veicolo,
        "nuovo_stato": data.nuovo_stato_veicolo
    }


# --- Authorize managers and aggregate completed-rental data with pandas and NumPy. ---
@router.get("/api/backoffice/analytics/kpi", tags=["Analytics"])
def get_fleet_kpi(current_user: dict=Depends(get_current_user)):
    """
    calculate Fleet key performance indicators (kpi) using pandas and numpy
    extracts completed rentals to compute revenues, averages, and statistical deviations
    """
    if current_user.get("role") not in ["manager"]:
        raise HTTPException(status_code=403, detail="Accesso riservato ai manager")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            #fetch all completed rentals with vehicle detail
            cur.execute("""
                SELECT n.codicenoleggio, n.veicolo, v.statooperativo, n.costototale, n.dataorainizio, n.dataorafine 
                FROM Noleggio n
                JOIN Veicolo v ON n.veicolo = v.serialeveicolo
                WHERE n.dataorafine IS NOT NULL;
            """)
            rows = cur.fetchall()

    # Return a clear result when there are no completed rentals to aggregate or export.
    if not rows:
        return {"message": "Nessun dato sufficiente per calcolare i KPI."}

    #1. load data into a Pandas Dataframe
    df= pd.DataFrame(rows)

    #ensure costototale is a numeric float for Numpy operations
    df['costototale'] = pd.to_numeric(df['costototale'])

    #2. pandas operations: grouping and aggregation
    total_revenue= df['costototale'].sum()
    revenue_by_vehicle=df.groupby('veicolo')['costototale'].sum().to_dict()

    #3. numpy operations: advanced statistical analysys
    #let's find the average rental cost and the standard deviation to spot anomalies
    avg_cost=np.mean(df['costototale'])
    std_deviation=np.std(df['costototale'])

    return{
        "kpi_summary":{
            "total_rentals_completed": len(df),
            "total_revenue_euro": round(float(total_revenue), 2),
            "average_rental_cost_euro": round(float(avg_cost),2),
            "cost_standand_deviation": round(float(std_deviation),2)
        },
        "revenue_by_vehicle": revenue_by_vehicle
    }


# --- Authorize managers and stream completed rentals as an in-memory Excel workbook. ---
@router.get("/api/backoffice/reports/export", tags=["Analytics"])
def export_rental_excel(current_user:dict =Depends(get_current_user)):
    """
    Export all completed rentals as a downloadable Excel (.xlsx) file for accuonting 
    uses pandas to structure the dataframe and OpenPyXL to generate the file in-memory
    """
    if current_user.get("role") not in ["manager"]:
        raise HTTPException(status_code=403, detail="Accesso riservato ai manager")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Noleggio WHERE dataorafine IS NOT NULL;")
            rows=cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Nessun noleggio da esportare.")

    df=pd.DataFrame(rows)

    #create an in-memory buffer to save the Excel file without writing to the pshysical disk
    output=io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Noleggi Completati')

    #rewind the buffer to the beginning so it can be read by FastAPI
    output.seek(0)

    #set headers to force the browser to download the file
    headers={ 
        'Content-Disposition': 'attachment; filename="ecofleet_rentals_report.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
