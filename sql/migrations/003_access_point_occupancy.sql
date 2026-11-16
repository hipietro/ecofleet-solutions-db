-- File overview
-- Purpose: Record the current vehicle occupying a charging slot without treating unknown slots as free.
-- Responsibilities: Preserve existing points, distinguish verified occupancy from missing data and
--   prevent the same vehicle from being assigned to multiple points.
-- Connections: Extends PuntoAccesso and references Veicolo from sql/ecofleet.sql; the rental
--   workflows and station-availability endpoints will use this state in subsequent increments.
-- Apply once per database, after migrations 001 and 002.

-- Transaction: apply the occupancy model as one schema change.
BEGIN;

-- existing points start with unknown occupancy and no assigned vehicle
ALTER TABLE PuntoAccesso
    ADD COLUMN veicolo INTEGER,
    ADD COLUMN occupazione_verificata BOOLEAN NOT NULL DEFAULT FALSE,

    -- an assigned vehicle must exist in the fleet.
    ADD CONSTRAINT puntoaccesso_veicolo_fk
        FOREIGN KEY (veicolo)
        REFERENCES Veicolo(serialeveicolo)
        ON DELETE RESTRICT,

    -- a vehicle can occupy at most one access point
    ADD CONSTRAINT puntoaccesso_veicolo_unique
        UNIQUE (veicolo),

    -- an assignment requires explicitly verified occupancy
    ADD CONSTRAINT puntoaccesso_occupazione_check
        CHECK (veicolo IS NULL OR occupazione_verificata);

COMMIT;
