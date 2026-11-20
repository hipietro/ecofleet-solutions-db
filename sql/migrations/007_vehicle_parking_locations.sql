-- File overview
-- Purpose: Define one current parking location for a vehicle, in a station or on the street.
-- Responsibilities: Validate complete station references or street coordinates and prevent
--   duplicate assignments for the same vehicle or charging point.
-- Connections: References Veicolo and PuntoAccesso. Rental history remains in Noleggio.
--   Existing slot assignments will move to this table when their readers and writers switch.
-- Apply once per database after migration 006.

BEGIN;

-- Store one confirmed parking location per vehicle.
CREATE TABLE PosizioneParcheggio (
    veicolo INTEGER PRIMARY KEY
        REFERENCES Veicolo(serialeveicolo) ON DELETE RESTRICT,
    codicehub INTEGER,
    numerostazione INTEGER,
    numeropunto INTEGER,
    latitudine NUMERIC(9,6),
    longitudine NUMERIC(9,6),
    tipo_luogo TEXT GENERATED ALWAYS AS (
        CASE WHEN codicehub IS NOT NULL THEN 'stazione' ELSE 'strada' END
    ) STORED,

    -- A station location references a complete access point.
    CONSTRAINT posizione_parcheggio_punto_fk
        FOREIGN KEY (codicehub, numerostazione, numeropunto)
        REFERENCES PuntoAccesso(codicehub, numerostazione, numeropunto)
        MATCH FULL ON DELETE RESTRICT,

    -- A charging point can hold only one parked vehicle.
    CONSTRAINT posizione_parcheggio_punto_unique
        UNIQUE (codicehub, numerostazione, numeropunto)
);

-- Require street coordinates only when no station point is assigned.
ALTER TABLE PosizioneParcheggio
    ADD CONSTRAINT posizione_parcheggio_luogo_check CHECK (
        CASE WHEN tipo_luogo = 'stazione' THEN
            latitudine IS NULL AND longitudine IS NULL
        ELSE
            latitudine IS NOT NULL AND latitudine BETWEEN -90 AND 90
            AND longitudine IS NOT NULL AND longitudine BETWEEN -180 AND 180
        END
    );

COMMIT;
