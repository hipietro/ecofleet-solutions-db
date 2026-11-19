-- File overview
-- Purpose: Support station and street return locations in rental history.
-- Responsibilities: Preserve existing station references, derive the return location type
--   and validate the location and billing data of active and completed rentals.
-- Connections: Extends Noleggio from sql/ecofleet.sql. Future rental operations will supply
--   confirmed return locations and update the vehicle's current parking position separately.
-- Apply once per database after migration 004.

BEGIN;

-- Store street return coordinates and derive the return location type.
ALTER TABLE Noleggio
    ADD COLUMN latitudine_fine NUMERIC(9,6),
    ADD COLUMN longitudine_fine NUMERIC(9,6),
    ADD COLUMN tipo_luogo_fine TEXT GENERATED ALWAYS AS (
        CASE
            WHEN dataorafine IS NULL THEN NULL
            WHEN hubfine IS NOT NULL THEN 'stazione'
            ELSE 'strada'
        END
    ) STORED;

-- Keep billing checks separate from return location checks.
ALTER TABLE Noleggio
    DROP CONSTRAINT noleggio_check1,
    ADD CONSTRAINT noleggio_dati_chiusura_check CHECK (
        (dataorafine IS NULL AND kmpercorsi IS NULL AND costototale IS NULL)
        OR (
            dataorafine IS NOT NULL
            AND kmpercorsi IS NOT NULL AND kmpercorsi >= 0
            AND costototale IS NOT NULL AND costototale >= 0
        )
    ),

    -- Require the right location fields for each rental state.
    ADD CONSTRAINT noleggio_luogo_fine_check CHECK (
        CASE
            WHEN tipo_luogo_fine IS NULL THEN
                hubfine IS NULL AND stazionefine IS NULL AND puntofine IS NULL
                AND latitudine_fine IS NULL AND longitudine_fine IS NULL
            WHEN tipo_luogo_fine = 'stazione' THEN
                hubfine IS NOT NULL AND stazionefine IS NOT NULL AND puntofine IS NOT NULL
                AND latitudine_fine IS NULL AND longitudine_fine IS NULL
            ELSE
                hubfine IS NULL AND stazionefine IS NULL AND puntofine IS NULL
                AND latitudine_fine IS NOT NULL AND latitudine_fine BETWEEN -90 AND 90
                AND longitudine_fine IS NOT NULL AND longitudine_fine BETWEEN -180 AND 180
        END
    );

COMMIT;
