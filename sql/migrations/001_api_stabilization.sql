-- File overview
-- Purpose: Upgrade the academic schema for the current FastAPI account and rental workflows.
-- Responsibilities: Add missing account fields, align roles, enforce active-rental uniqueness and unify billing.
-- Connections: Extends sql/ecofleet.sql; auth/corporate routes use the new fields, and rentals uses the price
--   returned by calcola_costo_noleggio. The existing HTTP integration suite also applies this migration.

-- Apply after sql/ecofleet.sql, or to an existing EcoFleet database.
-- This migration preserves existing rows and can be applied more than once.
-- Transaction section: apply all schema and function updates together.
BEGIN;

-- Account fields section: preserve existing rows while adding API-specific data when missing.
ALTER TABLE Cliente
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS ruolo VARCHAR(20) NOT NULL DEFAULT 'customer',
    ADD COLUMN IF NOT EXISTS saldo_crediti NUMERIC(10,2) NOT NULL DEFAULT 50.00,
    ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS default_payment_method VARCHAR(255);

-- Role section: synchronize the stored role vocabulary with authentication and staff/company routes.
ALTER TABLE Cliente DROP CONSTRAINT IF EXISTS cliente_ruolo_check;
ALTER TABLE Cliente ADD CONSTRAINT cliente_ruolo_check
    CHECK (ruolo IN ('customer', 'manager', 'technician', 'corporate'));

-- Enforce active-rental uniqueness even for concurrent SQL clients.
CREATE UNIQUE INDEX IF NOT EXISTS uq_noleggio_cliente_attivo
    ON Noleggio (cliente) WHERE dataorafine IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_noleggio_veicolo_attivo
    ON Noleggio (veicolo) WHERE dataorafine IS NULL;

-- Billing section: replace the baseline trigger body without repricing already-completed rentals.
CREATE OR REPLACE FUNCTION calcola_costo_noleggio()
RETURNS trigger AS $$
-- Billing inputs: use PostgreSQL numeric arithmetic and the existing one-euro unlock fee.
DECLARE
    v_durata_secondi NUMERIC;
    v_minuti NUMERIC;
    v_costo_orario NUMERIC;
    v_fattore_sconto NUMERIC;
    v_costo_sblocco CONSTANT NUMERIC := 1.00;
BEGIN
    -- Completion transition: price only the first change from active to completed.
    IF NEW.dataorafine IS NOT NULL AND OLD.dataorafine IS NULL THEN
        v_durata_secondi := EXTRACT(EPOCH FROM (NEW.dataorafine - NEW.dataorainizio));
        -- Duration validation: reject non-positive rentals before any amount is persisted.
        IF v_durata_secondi <= 0 THEN
            RAISE EXCEPTION 'La durata del noleggio deve essere positiva.';
        END IF;

        -- Each vehicle has its own hourly rate in its subtype table.
        v_minuti := GREATEST(1, CEIL(v_durata_secondi / 60));
        v_costo_orario := get_costo_orario_veicolo(NEW.veicolo);
        v_fattore_sconto := get_fattore_sconto_cliente(NEW.cliente);

        -- Apply the corporate discount to usage and unlocking together.
        NEW.costototale := ROUND(
            (v_costo_sblocco + v_minuti * v_costo_orario / 60) * v_fattore_sconto, 2
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Commit section: make the account, uniqueness and billing changes visible together.
COMMIT;
