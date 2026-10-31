# Stabilizzazione del backend EcoFleet

## 1. Il problema di partenza

La copia locale conteneva una route `/api/rentals/me` scritta come se esistesse un ORM SQLAlchemy. Il progetto usa invece psycopg e SQL esplicito: mancavano sia SQLAlchemy sia i modelli e la sessione citati dalla route. Questo impediva di importare e avviare l'applicazione.

La route ora esegue una query SQL parametrizzata. Il cliente viene identificato dal token validato e dal corrispondente account nel database, senza accettare un identificativo cliente dalla richiesta. Gli altri noleggi rimangono esclusi dalla risposta. La dashboard e i tipi TypeScript usano gli stessi nomi di campo dell'API.

## 2. La tariffa appartiene al singolo veicolo

`costoorario` non è una colonna di `Veicolo`: è nelle tabelle dei sottotipi, ciascuna collegata al singolo veicolo. La funzione PostgreSQL `get_costo_orario_veicolo(seriale)` recupera quella tariffa. Due auto della stessa categoria possono quindi avere prezzi diversi.

È stata eliminata anche la seconda definizione di `VehicleResponse`, che faceva divergere gli schemi di lista e dettaglio. I filtri SQL ora separano correttamente le condizioni e l'ordinamento con spazi.

## 3. Un solo calcolo per costo, wallet e ricevuta

La regola attuale è:

```text
minuti = massimo tra 1 e minuti iniziati, arrotondati per eccesso
costo = arrotonda_a_2_decimali((1 € + minuti × tariffa_oraria_del_veicolo / 60) × fattore_contratto)
```

Lo sblocco di 1 € deriva dal codice preesistente. Lo sconto si applica al totale, incluso lo sblocco. I fattori corporate già presenti nel database sono: Base 1,00; Silver 0,95; Gold 0,90; Premium 0,85. Il livello viene assegnato al contratto; non è calcolato automaticamente dal numero di dipendenti. Le nuove registrazioni rifiutano livelli sconosciuti, che altrimenti non riceverebbero alcuno sconto.

Esempio: auto a 120 €/ora, durata 61 secondi, contratto Premium. Si addebitano due minuti: `(1 + 2 × 120 / 60) × 0,85 = 4,25 €`.

Il trigger PostgreSQL calcola l'importo; l'API lo legge con `UPDATE ... RETURNING` e addebita esattamente quel valore. I noleggi già conclusi non vengono ricalcolati dalla migrazione.

## 4. Transazioni e richieste simultanee

La chiusura aggiorna noleggio, ricevuta, chilometraggio, saldo e stato del veicolo nella stessa transazione: se un passaggio fallisce, PostgreSQL annulla tutti gli aggiornamenti. Il chilometraggio viene modificato soltanto dal trigger, evitando il precedente doppio incremento.

`SELECT ... FOR UPDATE` blocca temporaneamente le righe interessate fino al termine della transazione. Le richieste per lo stesso cliente o veicolo vengono così coordinate. Gli indici unici parziali impediscono inoltre due noleggi attivi per cliente o veicolo anche a chi scrive direttamente nel DB.

Il wallet rimane virtuale: non è stato integrato un servizio di pagamento. Se il credito non basta alla chiusura, la richiesta viene rifiutata e il noleggio resta attivo fino alla ricarica. L'avvio richiede almeno 5 € e batteria almeno al 15%.

## 5. Altre correzioni

- La registrazione privata salva il telefono, anziché il cognome nella colonna `telefono`, e gestisce i duplicati di email, codice fiscale e patente in modo atomico.
- La registrazione corporate salva la data richiesta dal DB e usa un ruolo ammesso dalla migrazione.
- I ruoli per le autorizzazioni vengono riletti dal DB: un ruolo vecchio nel token non mantiene privilegi revocati.
- Il profilo restituisce la presenza effettiva di un metodo di pagamento, che in questa fase è soltanto un identificativo simulato.
- La manutenzione usa `Tecnico.matricola` e il ruolo `technician`, coerenti con il database.
- Le password oltre il limite bcrypt di 72 byte UTF-8 vengono rifiutate con errore di validazione. Un hash legacy non valido non causa un errore interno al login.

## 6. Aggiornamento del database

Il database locale verificato è PostgreSQL 18. Il vecchio script SQL non conteneva le colonne aggiunte per l'API. La migrazione conserva i dati e aggiunge colonne mancanti, vincoli e il calcolo concordato:

```bash
psql -h localhost -U postgres -d ecofleet -v ON_ERROR_STOP=1 -f sql/migrations/001_api_stabilization.sql
```

Il file `sql/ecofleet.sql` contiene istruzioni `DROP` ed è destinato all'inizializzazione di un database nuovo, non all'aggiornamento di quello in uso. Non eseguirlo sul database con i propri dati. Per una nuova installazione, eseguire prima quello script e poi la migrazione.

## 7. Test ripetibili

Dalla directory del progetto, con le dipendenze Python già installate:

```bash
ECOFLEET_RUN_DB_TESTS=1 venv/bin/python -m unittest discover -s backend/tests -v
```

La suite usa `unittest`, incluso in Python, senza nuovi framework. Richiede PostgreSQL locale e un utente con permesso di creare database. Legge host, porta e credenziali dalla configurazione locale, crea un DB dal nome casuale `ecofleet_test_...` e avvia un server API su una porta libera. Il database configurato in `DB_NAME` non viene usato dai test. Al termine, il server di test viene fermato e soltanto il database generato viene eliminato. I server remoti sono rifiutati. Se il processo viene interrotto forzatamente, può restare il database temporaneo da rimuovere dopo averne verificato il nome.

Sono test di integrazione HTTP: inviano richieste reali all'API e verificano anche gli effetti su PostgreSQL. Coprono tariffe individuali, sconto corporate, autenticazione e ruoli, registrazione, storico, transazioni annullate, batteria e richieste simultanee. Non sono test unitari con un database simulato: includono i trigger SQL reali del repository.

Le correzioni funzionali sono state completate prima del riordino delle directory. Il successivo refactoring della issue #17 è descritto nella [guida alla struttura](struttura_progetto.md); questa pagina documenta le correzioni precedenti.

## 8. Risultati verificati

Il 31 ottobre 2026 sono passati 15 test di integrazione HTTP con PostgreSQL reale, la compilazione TypeScript/Vite e il controllo ESLint. Il server locale in uso risponde con HTTP 200 a `/health` e alla ricerca filtrata dei veicoli. La migrazione è stata applicata anche al DB locale, dopo un salvataggio dello schema precedente: i conteggi di clienti, veicoli, noleggi, ricevute e aziende sono rimasti invariati. Nessun database temporaneo di test è rimasto sul server.

Le modifiche sono locali; non sono stati creati commit o eseguiti push. Le modifiche già presenti nel progetto sono state conservate e corrette dove impedivano il funzionamento dei flussi coinvolti.
