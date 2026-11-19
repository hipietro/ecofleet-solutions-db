-- File overview
-- Purpose: Represent station and street pickup locations in rental history.
-- Responsibilities: Preserve existing departures, validate the fields for each location type
--   and restrict connector checks to endpoints that reference a charging access point.
-- Connections: Extends Noleggio and its connector trigger from sql/ecofleet.sql. Migration 005
--   provides return locations, and future rental operations will record actual pickup locations.
-- Apply once per database after migration 005.

BEGIN;

-- Store either a complete station access point or street coordinates for pickup.
ALTER TABLE Noleggio
    ALTER COLUMN hubinizio DROP NOT NULL,
    ALTER COLUMN stazioneinizio DROP NOT NULL,
    ALTER COLUMN puntoinizio DROP NOT NULL,
    ADD COLUMN latitudine_inizio NUMERIC(9,6),
    ADD COLUMN longitudine_inizio NUMERIC(9,6),
    ADD COLUMN tipo_luogo_inizio TEXT GENERATED ALWAYS AS (
        CASE WHEN hubinizio IS NOT NULL THEN 'stazione' ELSE 'strada' END
    ) STORED,
    ADD CONSTRAINT noleggio_luogo_inizio_check CHECK (
        CASE WHEN tipo_luogo_inizio = 'stazione' THEN
            stazioneinizio IS NOT NULL AND puntoinizio IS NOT NULL
            AND latitudine_inizio IS NULL AND longitudine_inizio IS NULL
        ELSE
            stazioneinizio IS NULL AND puntoinizio IS NULL
            AND latitudine_inizio IS NOT NULL AND latitudine_inizio BETWEEN -90 AND 90
            AND longitudine_inizio IS NOT NULL AND longitudine_inizio BETWEEN -180 AND 180
        END
    );

-- Replace the existing trigger function while retaining its station compatibility checks.
CREATE OR REPLACE FUNCTION verifica_compatibilita_connettore()
RETURNS TRIGGER AS $$
DECLARE
    v_tipo_richiesto VARCHAR(30);
    v_tipo_inizio VARCHAR(30);
    v_tipo_fine VARCHAR(30);
BEGIN
    v_tipo_richiesto := get_tipo_connettore_veicolo(NEW.veicolo);

    -- Check the pickup connector only when the rental starts at a station.
    IF NEW.hubinizio IS NOT NULL THEN
        SELECT tipoconnettore
        INTO v_tipo_inizio
        FROM PuntoAccesso
        WHERE codicehub = NEW.hubinizio AND numerostazione = NEW.stazioneinizio AND numeropunto = NEW.puntoinizio;

        IF v_tipo_inizio IS NULL THEN
            RAISE EXCEPTION 'Punto iniziale inesistente: Hub %, Stazione %, Punto %.',
                NEW.hubinizio, NEW.stazioneinizio, NEW.puntoinizio;
        END IF;

        IF v_tipo_inizio <> v_tipo_richiesto THEN
            RAISE EXCEPTION 'Punto iniziale incompatibile con il veicolo %. Tipo richiesto %, trovato %.',
                NEW.veicolo, v_tipo_richiesto, v_tipo_inizio;
        END IF;
    END IF;

    -- Independently check the return connector when a complete station slot is provided.
    IF NEW.hubfine IS NOT NULL AND NEW.stazionefine IS NOT NULL AND NEW.puntofine IS NOT NULL THEN
        SELECT tipoconnettore
        INTO v_tipo_fine
        FROM PuntoAccesso
        WHERE codicehub = NEW.hubfine AND numerostazione = NEW.stazionefine AND numeropunto = NEW.puntofine;

        IF v_tipo_fine IS NULL THEN
            RAISE EXCEPTION 'Punto finale inesistente: Hub %, Stazione %, Punto %.',
                NEW.hubfine, NEW.stazionefine, NEW.puntofine;
        END IF;

        IF v_tipo_fine <> v_tipo_richiesto THEN
            RAISE EXCEPTION 'Punto finale incompatibile con il veicolo %. Tipo richiesto %, trovato %.',
                NEW.veicolo, v_tipo_richiesto, v_tipo_fine;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMIT;
