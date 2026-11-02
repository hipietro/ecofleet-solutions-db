/*
 * File overview
 * Purpose: Run the original academic EcoFleet reports from a standalone C terminal client.
 * Responsibilities: Connect with libpq, dispatch menu-selected SQL, format result tables and free resources.
 * Connections: Uses dependencies/include/libpq-fe.h and the bundled native libraries documented in README.txt;
 *   queries the schema from sql/ecofleet.sql directly and does not call the FastAPI application.
 */

// --- System and PostgreSQL client headers ---
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "dependencies/include/libpq-fe.h"

// --- Local PostgreSQL connection constants ---
// Adjust these demonstration values for the database used by this standalone client.

#define PG_HOST "localhost"
#define PG_USER "postgres"
#define PG_DB "EcoFleet_DB"
#define PG_PASS "password"
#define PG_PORT 5432


// --- Result formatting: print column names, values and row counts for any SELECT result ---
void stampa_tabella(PGresult *res) {
    int righe = PQntuples(res);
    int colonne = PQnfields(res);

    if (righe == 0) {
        printf("\n[Nessun record trovato per questa ricerca]\n\n");
        return;
    }

    printf("\n");

    // Reserve a consistent column width for readable report output.
    for (int j = 0; j < colonne; j++) {
        printf("%-24s | ", PQfname(res, j));
    }
    printf("\n");

    for (int j = 0; j < colonne; j++) {
        printf("---------------------------");
    }
    printf("\n");

    for (int i = 0; i < righe; i++) {
        for (int j = 0; j < colonne; j++) {
            printf("%-24s | ", PQgetvalue(res, i, j));
        }
        printf("\n");
    }

    printf("\nTotale record trovati: %d\n\n", righe);
}

// --- Query execution: check libpq result status, print rows and release the result object ---
void esegui_opzione(PGconn *conn, const char *query, const char *titolo) {
    printf("\n=== %s ===\n", titolo);

    PGresult *res = PQexec(conn, query);

    // Reject failed queries before attempting to format a table.
    if (PQresultStatus(res) != PGRES_TUPLES_OK) {
        fprintf(stderr, "Errore durante l'esecuzione della query: %s\n", PQerrorMessage(conn));
        PQclear(res);
        return;
    }

    stampa_tabella(res);
    PQclear(res);
}

// --- Program entry: connect, serve menu requests and close the connection ---
int main(void) {

    // --- Connection section: build libpq parameters and stop early if the server cannot be reached ---
    char conninfo[250];
    sprintf(conninfo, "host=%s port=%d dbname=%s user=%s password=%s", PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASS);

    PGconn *conn = PQconnectdb(conninfo);

    if (PQstatus(conn) != CONNECTION_OK) {
        fprintf(stderr, "Connessione fallita: %s\n", PQerrorMessage(conn));
        PQfinish(conn);
        exit(1);
    }

    printf("===========================================\n");
    printf("   Benvenuto nel sistema EcoFleet_DB CLI   \n");
    printf("===========================================\n");

    int scelta = -1;

    // --- Interactive menu section: read a report choice and dispatch the corresponding SELECT ---
    while (scelta != 0) {
        printf("Seleziona la query da eseguire:\n");
        printf(" 1. Performance economiche e di utilizzo per Marca e Modello\n");
        printf(" 2. Clienti privati \"Top Spender\" (Spesa > 100 Euro)\n");
        printf(" 3. Popolarita' e costi medi per Hub di Partenza\n");
        printf(" 4. Analisi operativa dei veicoli attualmente in Manutenzione\n");
        printf(" 5. Classifica dei 5 veicoli con batterie piu' usurate\n");
        printf(" 0. Esci dall'applicazione\n");
        printf("Inserisci la tua scelta (0-5): ");

        // Recover from non-numeric input before dispatching the selected report.
        if (scanf("%d", &scelta) != 1) {
            printf("\n[!] Input non valido. Inserisci un numero.\n\n");
            while (getchar() != '\n');
            continue;
        }

        switch (scelta) {
            // Revenue and mileage report grouped by vehicle brand and model.
            case 1: {
                const char *q1 =
                    "SELECT v.marca, v.modello, "
                    "COUNT(n.codicenoleggio) AS numero_noleggi_totali, "
                    "SUM(n.costototale) AS ricavo_complessivo_euro, "
                    "SUM(n.kmpercorsi) AS km_totali_percorsi "
                    "FROM public.veicolo v "
                    "JOIN public.noleggio n ON v.serialeveicolo = n.veicolo "
                    "WHERE n.dataorafine IS NOT NULL "
                    "GROUP BY v.marca, v.modello "
                    "ORDER BY ricavo_complessivo_euro DESC;";
                esegui_opzione(conn, q1, "QUERY 1: Performance economiche per Marca/Modello");
                break;
            }

            // Individual-customer spending report above the academic threshold.
            case 2: {
                const char *q2 =
                    "SELECT cp.nome, cp.cognome, cp.cliente AS codice_fiscale, "
                    "COUNT(n.codicenoleggio) AS numero_noleggi, "
                    "SUM(n.costototale) AS spesa_totale_euro "
                    "FROM public.clienteprivato cp "
                    "JOIN public.noleggio n ON cp.cliente = n.cliente "
                    "WHERE n.dataorafine IS NOT NULL "
                    "GROUP BY cp.cliente, cp.nome, cp.cognome "
                    "HAVING SUM(n.costototale) > 100.00 "
                    "ORDER BY spesa_totale_euro DESC;";
                esegui_opzione(conn, q2, "QUERY 2: Clienti privati Top Spender (>100 Euro)");
                break;
            }

            // Starting-hub popularity and average completed-rental cost.
            case 3: {
                const char *q3 =
                    "SELECT h.citta, "
                    "COUNT(n.codicenoleggio) AS noleggi_partiti, "
                    "ROUND(AVG(n.costototale), 2) AS costo_medio_noleggio_euro "
                    "FROM public.hublogistico h "
                    "JOIN public.noleggio n ON h.codicehub = n.hubinizio "
                    "WHERE n.dataorafine IS NOT NULL "
                    "GROUP BY h.citta "
                    "ORDER BY noleggi_partiti DESC;";
                esegui_opzione(conn, q3, "QUERY 3: Analisi Hub di Partenza");
                break;
            }

            // Maintenance report joined to vehicle and technician details.
            case 4: {
                const char *q4 =
                    "SELECT v.targa, v.marca, v.modello, "
                    "m.dataoraintervento, m.tipointervento, "
                    "m.costo AS costo_intervento, m.esito, "
                    "t.nome AS nome_tecnico, t.cognome AS cognome_tecnico "
                    "FROM public.veicolo v "
                    "JOIN public.manutenzione m ON v.serialeveicolo = m.veicolo "
                    "JOIN public.tecnico t ON m.tecnico = t.matricola "
                    "WHERE v.statooperativo = 'In Manutenzione' "
                    "ORDER BY m.dataoraintervento DESC;";
                esegui_opzione(conn, q4, "QUERY 4: Veicoli attualmente in Manutenzione");
                break;
            }

            // Battery wear report ordered by recharge-cycle count.
            case 5: {
                const char *q5 =
                    "SELECT v.targa, v.marca, v.modello, "
                    "b.serialebatteria, b.cicliricarica, b.percentualebatteria "
                    "FROM public.veicolo v "
                    "JOIN public.batteria b ON v.serialeveicolo = b.veicolo "
                    "ORDER BY b.cicliricarica DESC "
                    "LIMIT 5;";
                esegui_opzione(conn, q5, "QUERY 5: Top 5 Batterie piu' usurate");
                break;
            }

            case 0:
                printf("\nChiusura delle connessioni in corso... Arrivederci!\n");
                break;

            default:
                printf("\n[!] Opzione non valida. Scegli un numero tra 0 e 5.\n\n");
                break;
        }

        // --- Menu pacing: wait for Enter before displaying the next prompt ---
        if (scelta != 0) {
            printf("Premi INVIO per tornare al menu...");
            while (getchar() != '\n'); // Wait for the user to press Enter.
            getchar();
            printf("\n------------------------------------------------------------\n\n");
        }
    }

    // --- Cleanup section: release the PostgreSQL connection before exiting ---
    PQfinish(conn);
    return 0;
}
