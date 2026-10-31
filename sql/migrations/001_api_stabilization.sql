-- Apply after sql/ecofleet.sql, or to an existing EcoFleet database.
-- This migration preserves existing rows and can be applied more than once.
BEGIN;

ALTER TABLE Cliente
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS ruolo VARCHAR(20) NOT NULL DEFAULT 'customer',
    ADD COLUMN IF NOT EXISTS saldo_crediti NUMERIC(10,2) NOT NULL DEFAULT 50.00,
    ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS default_payment_method VARCHAR(255);

ALTER TABLE Cliente DROP CONSTRAINT IF EXISTS cliente_ruolo_check;
ALTER TABLE Cliente ADD CONSTRAINT cliente_ruolo_check
    CHECK (ruolo IN ('customer', 'manager', 'technician', 'corporate'));

-- Enforce active-rental uniqueness even for concurrent SQL clients.
CREATE UNIQUE INDEX IF NOT EXISTS uq_noleggio_cliente_attivo
    ON Noleggio (cliente) WHERE dataorafine IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_noleggio_veicolo_attivo
    ON Noleggio (veicolo) WHERE dataorafine IS NULL;

CREATE OR REPLACE FUNCTION calcola_costo_noleggio()
RETURNS trigger AS $$
DECLARE
    v_durata_secondi NUMERIC;
    v_minuti NUMERIC;
    v_costo_orario NUMERIC;
    v_fattore_sconto NUMERIC;
    v_costo_sblocco CONSTANT NUMERIC := 1.00;
BEGIN
    IF NEW.dataorafine IS NOT NULL AND OLD.dataorafine IS NULL THEN
        v_durata_secondi := EXTRACT(EPOCH FROM (NEW.dataorafine - NEW.dataorainizio));
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

COMMIT;
