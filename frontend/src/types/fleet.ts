/**
 * File overview
 * Purpose: Describe the vehicle and rental payloads used by React pages.
 * Responsibilities: Give compile-time types to API data, including nullable details and Decimal
 *   values serialized as strings.
 * Connections: Mirrors backend/app/schemas/fleet.py and rentals.py; Fleet and Dashboard consume
 *   these interfaces.
 */

// --- Vehicle contract: fields returned by fleet endpoints and nested in rental-history records. ---
export interface Vehicle {
    serialeveicolo: number;
    targa: string | null;
    modello: string;
    marca: string;
    // --- Operational details and price; the backend serializes Decimal values as strings. ---
    statooperativo: string;
    kmtotali: number;
    costoorario: string;
    livello_batteria: number | null;
}

// --- Rental-history contract: link a rental to its vehicle details and lifecycle timestamps. ---
export interface Rental {
    codicenoleggio: number;
    veicolo: number;
    veicolo_dettagli: Vehicle | null;
    dataorainizio: string;
    dataorafine: string | null;
    costo_totale: string | null;
    stato: 'attivo' | 'completato';
}
