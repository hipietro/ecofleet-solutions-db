EcoFleet Solutions - Applicazione C

Questo archivio contiene il programma C per eseguire da terminale le cinque query del progetto EcoFleet Solutions.
Il programma utilizza la libreria libpq di PostgreSQL e mostra un menu testuale per scegliere la query da eseguire.

Il codice segue l’impostazione vista a laboratorio: include libpq tramite dependencies/include/libpq-fe.h, usa #define per i parametri di connessione, costruisce la stringa conninfo con sprintf() e si collega al database tramite PQconnectdb(conninfo).


=== Configurazione ===

Prima di compilare o eseguire il programma, aprire query_all.c e modificare i parametri di connessione:

#define PG_HOST "localhost"
#define PG_USER "postgres"
#define PG_DB "EcoFleet_DB"
#define PG_PASS "password"
#define PG_PORT 5432

Il valore "password" è solo 'placeholder' e deve essere sostituito con la password reale dell'utente PostgreSQL.


=== Cartella dependencies ===

La cartella dependencies deve trovarsi nella stessa directory di query_all.c.

Struttura prevista:

dependencies/
  include/
    libpq-fe.h
    postgres_ext.h

  lib/
    libpq.dll
    libpq.lib
    eventuali DLL aggiuntive richieste a runtime su Windows

I file principali sono quelli indicati a laboratorio per l’utilizzo di libpq. 
Nella cartella lib possono essere presenti anche DLL aggiuntive utili per evitare errori di librerie mancanti su Windows.


=== Compilazione su Windows con Visual Studio / MSVC ===

Il programma è stato testato su Windows tramite il terminale "x64 Native Tools Command Prompt for VS 2022", utilizzando i seguenti comandi:

  cl query_all.c /I"dependencies\include" /link /LIBPATH:"dependencies\lib" libpq.lib

  set PATH=%CD%\dependencies\lib;C:\Program Files\PostgreSQL\18\bin;%PATH%

  query_all.exe


=== Compilazione su Windows con gcc / MinGW ===

Dalla cartella del progetto, compilare con:

  gcc query_all.c -L dependencies\lib -lpq -o query_all

Prima dell'esecuzione:

  set PATH=%CD%\dependencies\lib;%PATH%

Poi eseguire:

  query_all

Se durante l'esecuzione vengono segnalate DLL mancanti, aggiungere al PATH anche la cartella bin dell'installazione PostgreSQL:

  set PATH=%CD%\dependencies\lib;<PERCORSO_BIN_POSTGRESQL>;%PATH%

=== Linux / macOS ===

Su Linux o macOS è possibile usare la libreria libpq installata nel sistema, adattando i percorsi di compilazione se necessario.

Esempio Linux:

  gcc query_all.c -o query_all -I /usr/include/postgresql -lpq

Esempio macOS (da adattare il path in base al proprio percorso di installazione)

  gcc query_all.c -o query_all -I/Applications/Postgres.app/Contents/Versions/latest/include -L/Applications/Postgres.app/Contents/Versions/latest/lib -lpq

Poi eseguire:

  ./query_all

Se si usa la libreria installata nel sistema, può essere necessario sostituire in query_all.c:

#include "dependencies/include/libpq-fe.h"

con:

#include <libpq-fe.h>


=== Utilizzo ===

Una volta avviato, il programma mostra un menu con cinque query disponibili.
Digitare un numero da 1 a 5 per eseguire una query.
Digitare 0 per terminare il programma.