-- File overview
-- Purpose: Create a dedicated demonstration vehicle and departure/return charging slots.
-- Responsibilities: Add clearly labelled fictional data without reassigning existing vehicles
--   or changing existing points; reject accidental repeat execution.
-- Connections: Requires migrations 001 through 004 and the base vehicle/battery triggers;
--   fleet endpoints expose these records for subsequent rental-workflow development.
-- Development-only seed: all DEMO locations and technical states are fictional, not telemetry.

BEGIN;

DO $$
DECLARE
    demo_hub INTEGER;
    demo_veicolo INTEGER;
BEGIN
    -- Prevent accidental creation of duplicate demonstration data.
    IF EXISTS (SELECT 1 FROM Veicolo WHERE targa = 'DEMO-EC01') THEN
        RAISE EXCEPTION 'Il veicolo DEMO esiste già.';
    END IF;

    -- Create a fictional hub without inventing real geographic coordinates.
    INSERT INTO HubLogistico (citta, indirizzo, nome)
    VALUES ('DEMO', 'Ubicazione fittizia', 'Hub DEMO EcoFleet')
    RETURNING codicehub INTO demo_hub;

    -- Create a dedicated electric car; the existing trigger creates its battery.
    INSERT INTO Veicolo (marca, modello, targa, statooperativo, kmtotali)
    VALUES ('DEMO', 'Elettrica DEMO', 'DEMO-EC01', 'Disponibile', 0)
    RETURNING serialeveicolo INTO demo_veicolo;

    INSERT INTO AutoElettrica
        (veicolo, autonomiakm, capacitabatteriakwh, costoorario)
    VALUES (demo_veicolo, 200, 50, 12);

    -- Create separate departure and return stations.
    INSERT INTO StazioneRicarica
        (codicehub, numerostazione, potenzakw, numerocolonnine, nome, indirizzo)
    VALUES
        (demo_hub, 1, 22, 1, 'DEMO Ritiro', 'Indirizzo fittizio'),
        (demo_hub, 2, 22, 1, 'DEMO Restituzione', 'Indirizzo fittizio');

    -- Set fictional, explicitly known occupancy and technical conditions.
    INSERT INTO PuntoAccesso
        (codicehub, numerostazione, numeropunto, tipoconnettore,
         veicolo, occupazione_verificata, operativo)
    VALUES
        (demo_hub, 1, 1, get_tipo_connettore_veicolo(demo_veicolo),
         demo_veicolo, TRUE, TRUE),
        (demo_hub, 2, 1, get_tipo_connettore_veicolo(demo_veicolo),
         NULL, TRUE, TRUE);

    RAISE NOTICE 'Creati hub DEMO % e veicolo DEMO %.',
        demo_hub, demo_veicolo;
END;
$$;

COMMIT;