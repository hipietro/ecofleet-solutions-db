-- File overview
-- Purpose: Record whether a charging access point is technically operational.
-- Responsibilities: Keep technical operability separate from occupancy and preserve NULL
--   for points whose technical condition has not been verified.
-- Connections: Extends PuntoAccesso after migration 003; fleet responses expose this value
--   and subsequent return checks will require a compatible, free and operational point.
-- Apply once per database, after migrations 001 through 003.

-- Existing points retain an unknown technical condition until verified.
BEGIN;

ALTER TABLE PuntoAccesso
    ADD COLUMN operativo BOOLEAN;

COMMIT;