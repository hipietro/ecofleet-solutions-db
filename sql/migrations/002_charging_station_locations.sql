-- File overview
-- Purpose: Give each charging station its own name, address and optional map coordinates.
-- Responsibilities: Preserve existing stations, validate coordinate ranges and require latitude
--   and longitude to be either both present or both absent.
-- Connections: Extends StazioneRicarica from sql/ecofleet.sql; future fleet endpoints will use
--   station locations to place parked vehicles on the map instead of using the hub address.

-- transaction: apply the complete schema change or roll it back on failure
BEGIN;

-- station details: unknown values remain NULL until real data is provided.
ALTER TABLE StazioneRicarica
    ADD COLUMN nome VARCHAR(100),
    ADD COLUMN indirizzo VARCHAR(200),
    ADD COLUMN latitudine NUMERIC(9,6),
    ADD COLUMN longitudine NUMERIC(9,6),

    -- coordinates must fall within valid geographic ranges.
    ADD CONSTRAINT stazione_latitudine_check
        CHECK (latitudine BETWEEN -90 AND 90),
    
    ADD CONSTRAINT stazione_longitudine_check
        CHECK (longitudine BETWEEN -180 AND 180),

    -- A location requires both coordinates; incomplete pairs are rejected.
    ADD CONSTRAINT stazione_coordinate_complete_check
        CHECK ((latitudine IS NULL) = (longitudine IS NULL));

COMMIT;

