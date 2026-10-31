export interface Vehicle {
    serialeveicolo: number;
    targa: string | null;
    modello: string;
    marca: string;
    statooperativo: string;
    kmtotali: number;
    costoorario: string;
    livello_batteria: number | null;
}

export interface Rental {
    codicenoleggio: number;
    veicolo: number;
    veicolo_dettagli: Vehicle | null;
    dataorainizio: string;
    dataorafine: string | null;
    costo_totale: string | null;
    stato: 'attivo' | 'completato';
} 
