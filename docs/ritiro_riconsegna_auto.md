<!--
File overview
Purpose: Define the customer and fleet workflows for hybrid electric-car rentals.
Responsibilities: Explain return modes, user-facing rules, the station bonus and acceptance scenarios.
Connections: The technical design translates these rules into PostgreSQL, FastAPI and React changes.
-->

# EcoFleet: ritiro e riconsegna delle auto

**Decisione di prodotto del 18 novembre 2026.** Le auto possono essere riconsegnate in una stazione di ricarica oppure in un parcheggio idoneo in strada. La riconsegna in stazione dà diritto a un bonus quando il punto conferma il collegamento dell’auto. Il **10%** è il valore iniziale concordato per la progettazione e la demo, da valutare prima di adottarlo come condizione commerciale.

Questo documento descrive il comportamento da costruire. Il backend attuale richiede ancora uno slot sia al ritiro sia alla restituzione. Il [mockup](dashboard_preview.png) rappresenta la direzione visiva precedente e illustra il percorso in stazione. Le due opzioni sono descritte qui. Il [disegno tecnico](progettazione_noleggio_ibrido.md) contiene dati, controlli, dipendenze e ordine di lavoro.

## 1. Il problema che vogliamo risolvere

La persona sceglie un’auto per raggiungere una destinazione. Se la sola possibilità di terminare il noleggio è una stazione di ricarica, può ritrovarsi lontano dalla destinazione oppure davanti a uno slot occupato. Permettere la riconsegna in strada rende il viaggio più flessibile. Incentivare le stazioni aiuta a riportare le auto dove possono essere ricaricate.

Il percorso funziona in entrambe le direzioni. Dopo una riconsegna in strada, il cliente successivo deve poter trovare e ritirare l’auto nello stesso luogo, purché sia noleggiabile. Dopo una riconsegna in stazione, il cliente successivo la trova allo slot riportato nella scheda.

### Cosa abbiamo deciso e cosa resta aperto

| Tema | Direzione |
| --- | --- |
| Riconsegna delle auto | Due modalità: in stazione con conferma del collegamento oppure in strada in un luogo ammesso |
| Ritiro delle auto | Stazione o strada, secondo la posizione corrente confermata dell’auto |
| Incentivo | Iniziamo con un bonus del 10% in stazione. In strada il bonus di riconsegna è zero |
| Simulazione | In sviluppo il backend può simulare il collegamento della colonnina e le informazioni fisiche del mezzo. In produzione queste informazioni richiedono fonti effettive |
| Mappa durante la corsa | Mostra la posizione del veicolo e del telefono, le possibili stazioni con i singoli slot e le aree in cui il servizio consente la riconsegna in strada |
| Altri mezzi | L’estensione a furgoni, scooter e bici si decide per categoria dopo aver definito le relative condizioni |
| Decisioni ancora aperte | Aree effettive e regole di sosta, soglie e fonte della telemetria, assistenza quando manca la conferma, politica di saldo insufficiente, condizioni commerciali definitive |

## 2. Le parole che useremo

| Termine | Significato | Esempio |
| --- | --- | --- |
| **Hub** | Raggruppamento delle stazioni di una città | Hub Milano |
| **Stazione** | Luogo fisico con più punti di accesso | Stazione Centrale |
| **Punto di accesso o slot** | Il singolo posto con presa che può essere occupato da un veicolo | Punto 3 della stazione Centrale |
| **Area di riconsegna** | Zona in cui EcoFleet permette di concludere in strada. Il singolo posto deve comunque essere adatto alla sosta | Area dimostrativa A |
| **Posizione corrente** | Dove il mezzo si trova ora quando è parcheggiato e da dove si può ritirare | Centrale, punto 3, oppure un parcheggio in strada |
| **Luogo storico** | Punto di partenza o arrivo registrato per una corsa specifica | Il punto 3 usato ieri, anche se oggi l’auto è altrove |
| **Collegamento confermato** | Riscontro riferito a questa auto, a questo punto e a questa riconsegna | La colonnina riconosce l’auto del viaggio appena parcheggiata |

Una stazione può avere punti occupati, liberi, fuori servizio o ancora da verificare. La disponibilità della stazione si calcola dai punti. Se una colonnina fisica serve più posti indipendenti, ogni posto gestibile conta come un punto di accesso.

**Esempio:** Centrale ha tre punti. Il primo ha già un’auto, il secondo è libero e compatibile, il terzo è libero ma fuori servizio. Sulla mappa possiamo mostrare **«1 punto disponibile per la tua auto»**. Selezionando la stazione si capisce perché gli altri due punti sono esclusi.

## 3. Prima della corsa: trovare e ritirare l’auto

1. Aprendo **Esplora**, il cliente vede i veicoli disponibili vicini in lista o sulla mappa. I veicoli in stazione possono essere raggruppati sotto il marker della stazione. Le auto parcheggiate in strada hanno la propria posizione di ritiro.
2. Nella scheda del veicolo il cliente vede il luogo, la tariffa, lo sblocco e le condizioni di restituzione. Per la stazione mostriamo un nome riconoscibile e il numero del punto. Per la strada mostriamo una posizione con sufficiente precisione e un’indicazione utile per trovare l’auto.
3. Alla conferma, il backend verifica che il mezzo sia ancora disponibile, che il cliente possa partire e che il luogo corrisponda alla collocazione corrente. Si applicano le verifiche esistenti, compresi credito e batteria.
4. Se il ritiro in stazione va a buon fine, il punto si libera quando il rilascio è confermato. Se il ritiro avviene in strada, l’auto esce dall’elenco dei veicoli parcheggiati e disponibili. In entrambi i casi parte la stessa esperienza di noleggio.

La scheda può essere aperta mentre un’altra persona ritira lo stesso mezzo. La conferma del backend decide chi riesce a partire. Dopo un esito negativo la schermata aggiorna la disponibilità e consente di scegliere un altro mezzo.

## 4. Durante la corsa: scegliere la destinazione

La mappa conserva i due indicatori separati per telefono e veicolo. Mostra le **stazioni di riconsegna** con il numero di punti utilizzabili per quella specifica auto. Toccare la stazione permette di identificare i singoli punti. Propongo di mostrare le **aree di riconsegna in strada** come zone sulla stessa mappa e di spiegare la scelta anche con testo, così resta comprensibile se la mappa si carica lentamente.

La disponibilità mostrata è quella osservata all’ultimo aggiornamento. Se una stazione si riempie mentre il cliente è in viaggio, l’app indica un’altra stazione oppure un’area in strada ammessa. Il bonus resta legato al collegamento confermato. Selezionare la stazione è una scelta di destinazione e la prenotazione dello slot resta una decisione di prodotto separata.

**Pausa** e **Termina** hanno effetti diversi. In pausa l’auto rimane riservata e il tempo di pausa costa il 50% della tariffa attiva. Terminare avvia una verifica di riconsegna. Un cliente che parcheggia per una sosta può riprendere il viaggio oppure scegliere di terminarlo se soddisfa le condizioni del luogo.

## 5. Riconsegna in stazione

1. Il cliente seleziona **Consegna in stazione** e individua uno slot compatibile e utilizzabile, anche in una stazione diversa da quella di partenza.
2. Parcheggia e collega l’auto. Un punto con occupazione sconosciuta, guasto noto o connettore incompatibile va escluso dai suggerimenti.
3. L’app mostra **«Verifica collegamento»** mentre il backend attende o verifica il riscontro. Il riscontro identifica questa auto e questo specifico punto. La vicinanza del GPS e la selezione nella mappa servono a orientarsi.
4. Quando la restituzione è accettata, l’app mostra il totale con il bonus. Il mezzo risulta parcheggiato allo slot. La sua visibilità come noleggiabile dipende dai controlli di disponibilità, batteria e condizioni operative.

La regola iniziale suggerita è premiare il collegamento confermato a un punto idoneo. L’energia effettivamente erogata può dipendere anche dallo stato di carica dell’auto. Va definito come gestire un collegamento riuscito seguito da un errore di ricarica, perché il cliente ha già eseguito l’azione richiesta. Nel frattempo, una conferma mancante o incoerente produce una spiegazione e consente di scegliere un’alternativa valida o chiedere assistenza.

## 6. Riconsegna in strada

1. Il cliente sceglie **Consegna in strada** e vede se si trova in un’area ammessa, le condizioni della sosta e il prezzo applicabile.
2. Propongo di usare una posizione recente e sufficientemente precisa del **veicolo** per controllare l’area. Dove il punto è vicino a un confine, il sistema può richiedere un segnale migliore o assistenza. Il telefono guida l’utente.
3. L’auto deve risultare ferma e chiusa. Il cliente conferma di aver parcheggiato in un posto idoneo. Un’area ammessa indica che il servizio accetta quella zona e il cliente deve comunque verificare le condizioni del singolo posto. La mappa può mostrare le esclusioni che conosciamo.
4. Il backend conferma la chiusura e registra le coordinate del parcheggio. Lo storico mostra la riconsegna in strada. L’auto compare per un nuovo ritiro quando è effettivamente noleggiabile.

Se la posizione è assente o il parcheggio non è ammesso, l’app spiega cosa manca e indica una zona alternativa, una stazione o l’assistenza. Al cliente serve un esito chiaro, specialmente se ha già chiuso l’auto e l’app perde la connessione. Al rientro deve poter controllare se il noleggio è finito senza ripetere un addebito.

## 7. Come presentare il prezzo

Il prezzo dipende ancora dal singolo veicolo. Il costo d’uso, l’eventuale tempo in pausa, lo sblocco e lo sconto corporate formano il prezzo della corsa secondo le condizioni approvate. Per il primo disegno del bonus partiamo da questa sequenza:

1. Si calcola il costo della corsa secondo le regole applicabili.
2. Si applica l’eventuale sconto corporate.
3. Sul totale risultante si applica il **10% di bonus** se il percorso di stazione viene confermato. In strada il bonus di riconsegna è **0%**.
4. Il server registra l’importo finale ai centesimi e indica nel riepilogo quanto è stato risparmiato. Wallet, storico e ricevuta mostrano l’importo registrato.

| Scenario | Calcolo illustrativo | Totale |
| --- | --- | ---: |
| Totale da 20 €, riconsegna in strada | 20 € con bonus di riconsegna pari a zero | 20,00 € |
| Totale da 20 €, collegamento confermato | 20 € × 0,90 | 18,00 € |
| Importo iniziale 20 €, corporate 15%, in strada | 20 € × 0,85 | 17,00 € |
| Importo iniziale 20 €, corporate 15%, in stazione | 20 € × 0,85 × 0,90 | 15,30 € |

La percentuale che il cliente vede durante la corsa deve corrispondere alla condizione applicata alla sua ricevuta, anche in caso di futuro cambio del listino. Il bonus può essere sperimentato osservando quante auto rientrano in stazione, quante restano con batteria bassa in strada e quanti interventi di recupero occorrono. Questi sono criteri di valutazione, da usare quando avremo dati.

## 8. Conseguenze per chi gestisce la flotta

Il gestore vede la distinzione tra veicoli in uso, veicoli parcheggiati in stazione e veicoli parcheggiati in strada. Un’auto con poca autonomia può richiedere recupero o ricarica prima di tornare visibile per il ritiro. Lo staff vede anche punti tecnicamente fuori servizio, occupazioni da verificare e restituzioni che richiedono assistenza.

La posizione usata per recuperare un veicolo è la posizione di parcheggio confermata. I dati storici e quelli della corsa seguono permessi e conservazione da definire. L’utente successivo ha bisogno di sapere dove ritirare l’auto parcheggiata. La disponibilità per il ritiro è distinta dalla visibilità del movimento durante il noleggio.

## 9. Come capire se il percorso funziona

| Caso | Risultato osservabile |
| --- | --- |
| Ritiro in stazione e riconsegna in un’altra | Il punto di partenza si libera, quello di arrivo riceve esattamente l’auto collegata e compare il bonus |
| Riconsegna in strada in area ammessa | La corsa si chiude al prezzo applicabile e l’auto noleggiabile compare nel luogo di sosta |
| Ritiro dell’auto lasciata in strada | Il nuovo cliente parte dalla posizione corrente e nello storico compare una partenza in strada |
| Punto pieno, guasto, incompatibile o con conferma di un altro mezzo | L’app spiega il motivo e offre alternative applicabili |
| Posizione vecchia, incerta o in zona esclusa | Viene mostrata la verifica mancante prima di confermare la chiusura |
| Risposta persa o conferma ripetuta | Il cliente recupera l’esito dal server. Il saldo e la ricevuta riflettono un solo addebito |
| Credito insufficiente dopo la restituzione fisica | Si applica la politica concordata per fermare il tempo e regolare il saldo. La scelta è ancora aperta |

Per seguire i prossimi passi, usa il [disegno tecnico](progettazione_noleggio_ibrido.md) e il [piano del percorso cliente](https://github.com/hipietro/ecofleet-solutions-db/issues/6).
