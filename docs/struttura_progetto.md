# Struttura del progetto EcoFleet

## 1. Separare i componenti

`backend/` contiene l'applicazione Python e le sue dipendenze. `frontend/` contiene l'applicazione React e i suoi manifesti npm. `legacy/c/` conserva il client C originale con README e librerie native: i percorsi relativi fra sorgente e dipendenze restano validi. Gli script PostgreSQL rimangono in `sql/`, la documentazione in `docs/`.

I file npm duplicati nella root sono stati rimossi dalla struttura del progetto perché la dipendenza `react-router-dom` è già dichiarata in `frontend/package.json`. Non è stato introdotto un workspace npm. Il bytecode Python generato non fa parte della nuova struttura: è escluso dal versionamento tramite le regole già presenti in `.gitignore`.

## 2. Assemblare l'applicazione

`backend/app/main.py` crea l'istanza FastAPI, registra CORS e collega i router. Non contiene più tutte le funzioni delle route. Il comando di avvio, dalla root del repository, è:

```bash
venv/bin/uvicorn backend.app.main:app --reload --port 8000
```

L'ambiente virtuale locale `venv/` può essere riutilizzato. Per installare le dipendenze in un ambiente nuovo:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r backend/requirements.txt
```

Le dipendenze Python non sono cambiate: è cambiata la collocazione del loro elenco.

## 3. Raggruppare le route

Le funzioni preesistenti sono raggruppate in `backend/app/api/routes/`:

| Modulo | Responsabilità |
| --- | --- |
| `system.py` | Stato del servizio |
| `auth.py` | Registrazione privata, login, profilo, wallet e metodo di pagamento |
| `fleet.py` | Lista e dettaglio veicoli |
| `rentals.py` | Avvio, chiusura e storico noleggi |
| `corporate.py` | Registrazione aziendale e dipendenti |
| `backoffice.py` | Manutenzione, statistiche ed esportazione |

Un `APIRouter` raccoglie le route di un modulo; `app.include_router(...)` le collega all'applicazione. Gli URL sono gli stessi di prima. La registrazione corporate continua ad avere il percorso `/api/auth/register/corporate`, anche se il suo codice risiede nel modulo corporate.

`backend/app/api/dependencies.py` contiene `get_current_user`: FastAPI la esegue tramite `Depends(...)` prima degli endpoint che richiedono autenticazione. È una dipendenza applicativa, mentre CORS è un middleware che interviene sulle richieste trasversalmente. Per questo si trovano in directory diverse.

## 4. Configurazione, database e sicurezza

`backend/app/core/config.py` carica il file `.env` dalla root del repository e raccoglie impostazioni DB, JWT e CORS. Le variabili già presenti nell'ambiente mantengono la precedenza sul file `.env`.

`backend/app/db/connection.py` apre le connessioni con psycopg e mantiene il formato a dizionario delle righe. Le query e le transazioni degli endpoint sono rimaste nelle funzioni esistenti.

`backend/app/core/security.py` conserva hashing e verifica delle password e generazione dei token nelle stesse forme preesistenti. La validazione del token resta nella dipendenza di autenticazione. `backend/app/middleware/cors.py` registra la stessa politica CORS già usata dall'app.

## 5. Schemi e percorso di una richiesta

Gli schemi Pydantic sono in `backend/app/schemas/`, raggruppati per area funzionale. I nomi e i campi dei modelli non sono cambiati. Gli schemi dei noleggi importano quelli dei veicoli per le risposte con dettagli annidati.

Esempio: una richiesta di chiusura noleggio raggiunge il router `rentals`; FastAPI valida la richiesta con lo schema e risolve l'utente con la dipendenza di autenticazione. La funzione esegue le query tramite la connessione PostgreSQL. Il database applica funzioni e trigger; FastAPI serializza il risultato secondo lo schema di risposta.

Questa organizzazione rende più facile trovare il codice, senza aggiungere servizi, ORM o nuove regole di business.

## 6. Test e frontend

La suite esistente è stata spostata in `backend/tests/`. Sono stati aggiornati soltanto il percorso della root e il modulo di avvio del server di test; non sono stati aggiunti nuovi test.

```bash
ECOFLEET_RUN_DB_TESTS=1 venv/bin/python -m unittest discover -s backend/tests -v
```

Il frontend continua a partire dalla propria directory:

```bash
cd frontend
npm run dev
```

Il refactoring è stato verificato confrontando la descrizione OpenAPI prima e dopo e rieseguendo i 15 test di integrazione esistenti. Lo schema e i dati del database locale non richiedono migrazioni per questi spostamenti.
