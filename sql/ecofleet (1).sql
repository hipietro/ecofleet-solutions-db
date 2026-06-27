DROP TABLE IF EXISTS Ricevuta CASCADE;
DROP TABLE IF EXISTS Noleggio CASCADE;
DROP TABLE IF EXISTS Manutenzione CASCADE;
DROP TABLE IF EXISTS Abilitazione CASCADE;
DROP TABLE IF EXISTS Certificazione CASCADE;
DROP TABLE IF EXISTS Tecnico CASCADE;
DROP TABLE IF EXISTS DipendenteCorporate CASCADE;
DROP TABLE IF EXISTS ClienteCorporate CASCADE;
DROP TABLE IF EXISTS ClientePrivato CASCADE;
DROP TABLE IF EXISTS Cliente CASCADE;
DROP TABLE IF EXISTS PuntoAccesso CASCADE;
DROP TABLE IF EXISTS StazioneRicarica CASCADE;
DROP TABLE IF EXISTS HubLogistico CASCADE;
DROP TABLE IF EXISTS Batteria CASCADE;
DROP TABLE IF EXISTS VeicoloLeggeroElettrico CASCADE;
DROP TABLE IF EXISTS FurgoneElettrico CASCADE;
DROP TABLE IF EXISTS AutoElettrica CASCADE;
DROP TABLE IF EXISTS Veicolo CASCADE;

DROP DOMAIN IF EXISTS tipopagamento CASCADE;
DROP DOMAIN IF EXISTS statomezzo CASCADE;
DROP DOMAIN IF EXISTS percentualebatteria CASCADE;
DROP DOMAIN IF EXISTS euro CASCADE;

DROP SEQUENCE IF EXISTS certificazione_codicecertificazione_seq CASCADE;
DROP SEQUENCE IF EXISTS hublogistico_idhub_seq CASCADE;
DROP SEQUENCE IF EXISTS noleggio_idnoleggio_seq CASCADE;
DROP SEQUENCE IF EXISTS ricevuta_id_ricevuta_seq CASCADE;
DROP SEQUENCE IF EXISTS veicolo_idveicolo_seq CASCADE;


SET client_encoding = 'UTF8';


-- DOMINI --

CREATE DOMAIN euro AS NUMERIC(8,2)
CHECK (VALUE >= 0);

CREATE DOMAIN percentualebatteria AS INTEGER
CHECK (VALUE >= 0 AND VALUE <= 100);

CREATE DOMAIN statomezzo AS VARCHAR(30)
CHECK (VALUE IN ('Disponibile', 'In Uso', 'In Manutenzione', 'In Carica'));

CREATE DOMAIN tipopagamento AS VARCHAR(30)
CHECK (VALUE IN (
  'Carta di Credito',
  'Carta di Debito',
  'PayPal',
  'Apple Pay',
  'Google Pay',
  'Satispay',
  'Bonifico Bancario')
);



-- VEICOLI --

CREATE TABLE Veicolo (
  serialeveicolo INTEGER PRIMARY KEY,
  marca VARCHAR(50) NOT NULL,
  modello VARCHAR(50) NOT NULL,
  targa VARCHAR(20) NOT NULL UNIQUE,
  statooperativo statomezzo NOT NULL,
  kmtotali INTEGER DEFAULT 0 CHECK (kmtotali >= 0)
);

CREATE TABLE AutoElettrica (
  veicolo INTEGER PRIMARY KEY,
  autonomiakm INTEGER NOT NULL CHECK (autonomiakm > 0),
  capacitabatteriakwh NUMERIC(6,2) NOT NULL CHECK (capacitabatteriakwh > 0),
  costoorario euro NOT NULL,
  FOREIGN KEY (veicolo) REFERENCES Veicolo(serialeveicolo) ON DELETE CASCADE
);

CREATE TABLE FurgoneElettrico (
  veicolo INTEGER PRIMARY KEY,
  autonomiakm INTEGER NOT NULL CHECK (autonomiakm > 0),
  capacitacarico NUMERIC(6,2) NOT NULL CHECK (capacitacarico > 0),
  costoorario euro NOT NULL,
  FOREIGN KEY (veicolo) REFERENCES Veicolo(serialeveicolo) ON DELETE CASCADE
);

CREATE TABLE VeicoloLeggeroElettrico (
  veicolo INTEGER PRIMARY KEY,
  necessitacolonnina BOOLEAN NOT NULL,
  costoorario euro NOT NULL,
  tipomezzo VARCHAR(30) DEFAULT 'Scooter' NOT NULL,
  FOREIGN KEY (veicolo) REFERENCES Veicolo(serialeveicolo) ON DELETE CASCADE
);

CREATE TABLE Batteria (
  serialebatteria VARCHAR(50) PRIMARY KEY,
  capacita NUMERIC(6,2) NOT NULL CHECK (capacita > 0),
  cicliricarica INTEGER DEFAULT 0 CHECK (cicliricarica >= 0),
  statobatteria statomezzo NOT NULL,
  veicolo INTEGER NOT NULL UNIQUE,
  percentualebatteria percentualebatteria DEFAULT 100 NOT NULL,
  FOREIGN KEY (veicolo) REFERENCES Veicolo(serialeveicolo) ON DELETE CASCADE
);


-- CLIENTI --

CREATE TABLE Cliente (
  codicefiscale VARCHAR(16) PRIMARY KEY,
  email VARCHAR(100) NOT NULL UNIQUE,
  telefono VARCHAR(20),
  dataregistrazione DATE NOT NULL
);

CREATE TABLE ClientePrivato (
  cliente VARCHAR(16) PRIMARY KEY,
  nome VARCHAR(50) NOT NULL,
  cognome VARCHAR(50) NOT NULL,
  patente VARCHAR(30) NOT NULL UNIQUE,
  FOREIGN KEY (cliente) REFERENCES Cliente(codicefiscale) ON DELETE CASCADE
);

CREATE TABLE ClienteCorporate (
  cliente VARCHAR(16) PRIMARY KEY,
  ragionesociale VARCHAR(100) NOT NULL,
  partitaiva VARCHAR(20) NOT NULL UNIQUE,
  livellocontratto VARCHAR(30) NOT NULL,
  FOREIGN KEY (cliente) REFERENCES Cliente(codicefiscale) ON DELETE CASCADE
);

CREATE TABLE DipendenteCorporate (
  clientecorporate VARCHAR(16) NOT NULL,
  codicedipendente VARCHAR(30) NOT NULL,
  nome VARCHAR(50) NOT NULL,
  cognome VARCHAR(50) NOT NULL,
  reparto VARCHAR(50),
  PRIMARY KEY (clientecorporate, codicedipendente),
  FOREIGN KEY (clientecorporate) REFERENCES ClienteCorporate(cliente) ON DELETE CASCADE
);


-- INFRASTRUTTURA --

CREATE TABLE HubLogistico (
  codicehub INTEGER PRIMARY KEY,
  citta VARCHAR(50) NOT NULL,
  indirizzo VARCHAR(100) NOT NULL,
  areaoperativa VARCHAR(100),
  nome VARCHAR(100)
);

CREATE TABLE StazioneRicarica (
  codicehub INTEGER NOT NULL,
  numerostazione INTEGER NOT NULL,
  potenzakw NUMERIC(6,2) NOT NULL CHECK (potenzakw > 0),
  numerocolonnine INTEGER NOT NULL CHECK (numerocolonnine > 0),
  PRIMARY KEY (codicehub, numerostazione),
  FOREIGN KEY (codicehub) REFERENCES HubLogistico(codicehub) ON DELETE CASCADE
);

CREATE TABLE PuntoAccesso (
  codicehub INTEGER NOT NULL,
  numerostazione INTEGER NOT NULL,
  numeropunto INTEGER NOT NULL,
  tipoconnettore VARCHAR(30) NOT NULL CHECK (tipoconnettore IN ('1', '2', '3')),
  PRIMARY KEY (codicehub, numerostazione, numeropunto),
  FOREIGN KEY (codicehub, numerostazione)
    REFERENCES StazioneRicarica(codicehub, numerostazione) ON DELETE CASCADE
);


-- TECNICI, CERTIFICAZIONI, MANUTENZIONI --

CREATE TABLE Tecnico (
  matricola VARCHAR(20) PRIMARY KEY,
  nome VARCHAR(50) NOT NULL,
  cognome VARCHAR(50) NOT NULL,
  specializzazione VARCHAR(50)
);

CREATE TABLE Certificazione (
  codicecertificazione INTEGER PRIMARY KEY,
  titolo VARCHAR(100) NOT NULL UNIQUE,
  ambito VARCHAR(100)
);

CREATE TABLE Abilitazione (
  tecnico VARCHAR(20) NOT NULL,
  certificazione INTEGER NOT NULL,
  datarilascio DATE NOT NULL,
  enterilascio VARCHAR(100) NOT NULL,
  PRIMARY KEY (tecnico, certificazione),
  FOREIGN KEY (tecnico) REFERENCES Tecnico(matricola) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (certificazione) REFERENCES Certificazione(codicecertificazione) ON DELETE CASCADE
);

CREATE TABLE Manutenzione (
  veicolo INTEGER NOT NULL,
  tecnico VARCHAR(20) NOT NULL,
  dataoraintervento DATE NOT NULL,
  tipointervento VARCHAR(50) NOT NULL,
  costo euro NOT NULL,
  esito VARCHAR(100),
  PRIMARY KEY (veicolo, tecnico, dataoraintervento),
  FOREIGN KEY (veicolo) REFERENCES Veicolo(serialeveicolo) ON DELETE CASCADE,
  FOREIGN KEY (tecnico) REFERENCES Tecnico(matricola) ON UPDATE CASCADE ON DELETE RESTRICT
);


-- NOLEGGI E RICEVUTE --

CREATE TABLE Noleggio (
  codicenoleggio INTEGER PRIMARY KEY,

  cliente VARCHAR(16) NOT NULL,
  veicolo INTEGER NOT NULL,

  dataorainizio TIMESTAMP(0) NOT NULL,
  dataorafine TIMESTAMP(0),

  costototale euro,
  kmpercorsi INTEGER,

  hubinizio INTEGER NOT NULL,
  stazioneinizio INTEGER NOT NULL,
  puntoinizio INTEGER NOT NULL,

  hubfine INTEGER,
  stazionefine INTEGER,
  puntofine INTEGER,

  FOREIGN KEY (cliente) REFERENCES Cliente(codicefiscale),
  FOREIGN KEY (veicolo) REFERENCES Veicolo(serialeveicolo) ON DELETE RESTRICT,

  FOREIGN KEY (hubinizio, stazioneinizio, puntoinizio)
    REFERENCES PuntoAccesso(codicehub, numerostazione, numeropunto) ON DELETE RESTRICT,

  FOREIGN KEY (hubfine, stazionefine, puntofine)
    REFERENCES PuntoAccesso(codicehub, numerostazione, numeropunto) ON DELETE SET NULL,

  UNIQUE (cliente, veicolo, hubinizio, stazioneinizio, puntoinizio, dataorainizio),

  CHECK (dataorafine IS NULL OR dataorafine >= dataorainizio),

  CHECK (
    (
      dataorafine IS NULL
      AND hubfine IS NULL
      AND stazionefine IS NULL
      AND puntofine IS NULL
      AND kmpercorsi IS NULL
      AND costototale IS NULL
    )
    OR
    (
      dataorafine IS NOT NULL
      AND hubfine IS NOT NULL
      AND stazionefine IS NOT NULL
      AND puntofine IS NOT NULL
      AND kmpercorsi IS NOT NULL
      AND costototale IS NOT NULL
      AND kmpercorsi >= 0
      AND costototale >= 0
    )
  )
);

CREATE TABLE Ricevuta (
  codicericevuta INTEGER PRIMARY KEY,
  noleggio INTEGER NOT NULL UNIQUE,
  dataemissione TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  metodopagamento tipopagamento DEFAULT 'Carta di Credito' NOT NULL,
  FOREIGN KEY (noleggio) REFERENCES Noleggio(codicenoleggio) ON DELETE CASCADE
);



-- SEQUENZE PER ID --

CREATE SEQUENCE veicolo_idveicolo_seq
  AS integer
  START WITH 1
  INCREMENT BY 1
  NO MINVALUE
  NO MAXVALUE
  CACHE 1;

ALTER SEQUENCE veicolo_idveicolo_seq OWNED BY Veicolo.serialeveicolo;
ALTER TABLE Veicolo ALTER COLUMN serialeveicolo SET DEFAULT nextval('veicolo_idveicolo_seq');

CREATE SEQUENCE hublogistico_idhub_seq
  AS integer
  START WITH 1
  INCREMENT BY 1
  NO MINVALUE
  NO MAXVALUE
  CACHE 1;

ALTER SEQUENCE hublogistico_idhub_seq OWNED BY  HubLogistico.codicehub;
ALTER TABLE HubLogistico ALTER COLUMN codicehub SET DEFAULT nextval('hublogistico_idhub_seq');

CREATE SEQUENCE certificazione_codicecertificazione_seq
  AS integer
  START WITH 1
  INCREMENT BY 1
  NO MINVALUE
  NO MAXVALUE
  CACHE 1;

ALTER SEQUENCE certificazione_codicecertificazione_seq OWNED BY Certificazione.codicecertificazione;
ALTER TABLE Certificazione ALTER COLUMN codicecertificazione SET DEFAULT nextval('certificazione_codicecertificazione_seq');

CREATE SEQUENCE noleggio_idnoleggio_seq
  AS integer
  START WITH 1
  INCREMENT BY 1
  NO MINVALUE
  NO MAXVALUE
  CACHE 1;

ALTER SEQUENCE noleggio_idnoleggio_seq OWNED BY Noleggio.codicenoleggio;
ALTER TABLE Noleggio ALTER COLUMN codicenoleggio SET DEFAULT nextval('noleggio_idnoleggio_seq');

CREATE SEQUENCE ricevuta_id_ricevuta_seq
  AS integer
  START WITH 1
  INCREMENT BY 1
  NO MINVALUE
  NO MAXVALUE
  CACHE 1;

ALTER SEQUENCE ricevuta_id_ricevuta_seq OWNED BY Ricevuta.codicericevuta;
ALTER TABLE Ricevuta ALTER COLUMN codicericevuta SET DEFAULT nextval('ricevuta_id_ricevuta_seq');


-- POPOLAMENTO DEL DB --

INSERT INTO Veicolo (serialeveicolo, marca, modello, targa, statooperativo, kmtotali) VALUES
  ('102', 'Tesla', 'Model Y', 'GK301AA', 'Disponibile', '5250'),
  ('103', 'Fiat', '500e', 'GK302AA', 'Disponibile', '6500'),
  ('104', 'Nissan', 'Leaf', 'GK303AA', 'Disponibile', '7750'),
  ('105', 'Hyundai', 'Ioniq 5', 'GK304AA', 'Disponibile', '9000'),
  ('106', 'Kia', 'EV6', 'GK305AA', 'Disponibile', '10250'),
  ('107', 'Dacia', 'Spring', 'GK306AA', 'Disponibile', '11500'),
  ('108', 'BMW', 'i4 M50', 'GK307AA', 'Disponibile', '12750'),
  ('109', 'Audi', 'Q4 e-tron', 'GK308AA', 'Disponibile', '14000'),
  ('110', 'Mercedes-Benz', 'EQA', 'GK309AA', 'Disponibile', '15250'),
  ('111', 'Polestar', '2', 'GK310AA', 'Disponibile', '16500'),
  ('112', 'Cupra', 'Born', 'GK311AA', 'In Uso', '17750'),
  ('113', 'MG', 'MG4 Electric', 'GK312AA', 'In Uso', '19000'),
  ('114', 'Ford', 'Mustang Mach-E', 'GK313AA', 'In Uso', '20250'),
  ('115', 'Volvo', 'XC40 Recharge', 'GK314AA', 'In Carica', '21500'),
  ('116', 'Porsche', 'Taycan', 'GK315AA', 'In Manutenzione', '22750'),
  ('117', 'Citroen', 'e-Berlingo', 'GL516BB', 'Disponibile', '25400'),
  ('118', 'Peugeot', 'e-Expert', 'GL517BB', 'Disponibile', '26300'),
  ('119', 'Toyota', 'Proace Electric', 'GL518BB', 'Disponibile', '27200'),
  ('120', 'Mercedes-Benz', 'eSprinter', 'GL519BB', 'Disponibile', '28100'),
  ('121', 'Renault', 'Kangoo E-Tech', 'GL520BB', 'Disponibile', '29000'),
  ('122', 'Iveco', 'eDaily', 'GL521BB', 'Disponibile', '29900'),
  ('123', 'Volkswagen', 'ID. Buzz Cargo', 'GL522BB', 'Disponibile', '30800'),
  ('124', 'Fiat', 'E-Ducato', 'GL523BB', 'Disponibile', '31700'),
  ('125', 'Opel', 'Combo-e', 'GL524BB', 'Disponibile', '32600'),
  ('126', 'Mercedes-Benz', 'eVito', 'GL525BB', 'Disponibile', '33500'),
  ('127', 'Renault', 'Master E-Tech', 'GL526BB', 'In Uso', '34400'),
  ('128', 'Citroen', 'e-Jumpy', 'GL527BB', 'In Uso', '35300'),
  ('129', 'Peugeot', 'e-Partner', 'GL528BB', 'In Uso', '36200'),
  ('130', 'Ford', 'E-Transit Custom', 'GL529BB', 'In Carica', '37100'),
  ('131', 'Fiat', 'E-Scudo', 'GL530BB', 'In Carica', '38000'),
  ('132', 'Piaggio', '1 Active', 'ED34131', 'Disponibile', '4210'),
  ('133', 'Vespa', 'Elettrica 70km/h', 'ED34132', 'Disponibile', '4320'),
  ('134', 'Silence', 'S01', 'ED34133', 'Disponibile', '4430'),
  ('135', 'Niu', 'NQi GTS', 'ED34134', 'Disponibile', '4540'),
  ('136', 'Super Soco', 'CPx', 'ED34135', 'Disponibile', '4650'),
  ('137', 'BMW', 'CE 04', 'ED34136', 'In Uso', '4760'),
  ('138', 'Seat', 'MO 125', 'ED34137', 'In Uso', '4870'),
  ('139', 'Segway', 'E125S', 'ED34138', 'In Carica', '4980'),
  ('140', 'Yadea', 'T9L Plus', 'ED34139', 'In Carica', '5090'),
  ('141', 'Kymco', 'Agility EV', 'ED34140', 'In Manutenzione', '5200'),
  ('142', 'Riese & Müller', 'Load 75 Touring', 'EB34141', 'Disponibile', '1850'),
  ('143', 'Trek', 'Allant+ 7', 'EB34142', 'Disponibile', '1420');


INSERT INTO HubLogistico (codicehub, citta, indirizzo, areaoperativa, nome) VALUES
  ('1', 'Milano', 'Via Vittor Pisani 15', 'Milano Centro-Stazione', 'Hub Milano'),
  ('2', 'Torino', 'Corso Vittorio Emanuele II 52', 'Torino Centro-Crocetta', 'Hub Torino'),
  ('3', 'Bologna', 'Piazza Medaglie d''Oro 2', 'Bologna Centro-Saffi', 'Hub Bologna'),
  ('4', 'Roma', 'Via Marsala 28', 'Roma Termini-Castro Pretorio', 'Hub Roma'),
  ('5', 'Firenze', 'Piazza della Stazione 4', 'Firenze Santa Maria Novella', 'Hub Firenze');


INSERT INTO StazioneRicarica (potenzakw, numerocolonnine, codicehub, numerostazione) VALUES
  ('150.00', '10', '1', '1'),
  ('50.00', '10', '1', '2'),
  ('22.00', '10', '1', '3'),
  ('100.00', '10', '2', '1'),
  ('22.00', '10', '2', '2'),
  ('150.00', '10', '3', '1'),
  ('50.00', '10', '3', '2'),
  ('150.00', '10', '4', '1'),
  ('100.00', '10', '4', '2'),
  ('50.00', '10', '4', '3'),
  ('100.00', '10', '5', '1'),
  ('22.00', '10', '5', '2');

INSERT INTO PuntoAccesso (numeropunto, tipoconnettore, codicehub, numerostazione) VALUES
  ('1', '2', '1', '1'),
  ('2', '3', '1', '1'),
  ('3', '1', '1', '1'),
  ('4', '2', '1', '1'),
  ('5', '3', '1', '1'),
  ('6', '1', '1', '1'),
  ('7', '2', '1', '1'),
  ('8', '3', '1', '1'),
  ('9', '1', '1', '1'),
  ('10', '2', '1', '1'),
  ('1', '2', '1', '2'),
  ('2', '3', '1', '2'),
  ('3', '1', '1', '2'),
  ('4', '2', '1', '2'),
  ('5', '3', '1', '2'),
  ('6', '1', '1', '2'),
  ('7', '2', '1', '2'),
  ('8', '3', '1', '2'),
  ('9', '1', '1', '2'),
  ('10', '2', '1', '2'),
  ('1', '2', '1', '3'),
  ('2', '3', '1', '3'),
  ('3', '1', '1', '3'),
  ('4', '2', '1', '3'),
  ('5', '3', '1', '3'),
  ('6', '1', '1', '3'),
  ('7', '2', '1', '3'),
  ('8', '3', '1', '3'),
  ('9', '1', '1', '3'),
  ('10', '2', '1', '3'),
  ('1', '2', '2', '1'),
  ('2', '3', '2', '1'),
  ('3', '1', '2', '1'),
  ('4', '2', '2', '1'),
  ('5', '3', '2', '1'),
  ('6', '1', '2', '1'),
  ('7', '2', '2', '1'),
  ('8', '3', '2', '1'),
  ('9', '1', '2', '1'),
  ('10', '2', '2', '1'),
  ('1', '2', '2', '2'),
  ('2', '3', '2', '2'),
  ('3', '1', '2', '2'),
  ('4', '2', '2', '2'),
  ('5', '3', '2', '2'),
  ('6', '1', '2', '2'),
  ('7', '2', '2', '2'),
  ('8', '3', '2', '2'),
  ('9', '1', '2', '2'),
  ('10', '2', '2', '2'),
  ('1', '2', '3', '1'),
  ('2', '3', '3', '1'),
  ('3', '1', '3', '1'),
  ('4', '2', '3', '1'),
  ('5', '3', '3', '1'),
  ('6', '1', '3', '1'),
  ('7', '2', '3', '1'),
  ('8', '3', '3', '1'),
  ('9', '1', '3', '1'),
  ('10', '2', '3', '1'),
  ('1', '2', '3', '2'),
  ('2', '3', '3', '2'),
  ('3', '1', '3', '2'),
  ('4', '2', '3', '2'),
  ('5', '3', '3', '2'),
  ('6', '1', '3', '2'),
  ('7', '2', '3', '2'),
  ('8', '3', '3', '2'),
  ('9', '1', '3', '2'),
  ('10', '2', '3', '2'),
  ('1', '2', '4', '1'),
  ('2', '3', '4', '1'),
  ('3', '1', '4', '1'),
  ('4', '2', '4', '1'),
  ('5', '3', '4', '1'),
  ('6', '1', '4', '1'),
  ('7', '2', '4', '1'),
  ('8', '3', '4', '1'),
  ('9', '1', '4', '1'),
  ('10', '2', '4', '1'),
  ('1', '2', '4', '2'),
  ('2', '3', '4', '2'),
  ('3', '1', '4', '2'),
  ('4', '2', '4', '2'),
  ('5', '3', '4', '2'),
  ('6', '1', '4', '2'),
  ('7', '2', '4', '2'),
  ('8', '3', '4', '2'),
  ('9', '1', '4', '2'),
  ('10', '2', '4', '2'),
  ('1', '2', '4', '3'),
  ('2', '3', '4', '3'),
  ('3', '1', '4', '3'),
  ('4', '2', '4', '3'),
  ('5', '3', '4', '3'),
  ('6', '1', '4', '3'),
  ('7', '2', '4', '3'),
  ('8', '3', '4', '3'),
  ('9', '1', '4', '3'),
  ('10', '2', '4', '3'),
  ('1', '2', '5', '1'),
  ('2', '3', '5', '1'),
  ('3', '1', '5', '1'),
  ('4', '2', '5', '1'),
  ('5', '3', '5', '1'),
  ('6', '1', '5', '1'),
  ('7', '2', '5', '1'),
  ('8', '3', '5', '1'),
  ('9', '1', '5', '1'),
  ('10', '2', '5', '1'),
  ('1', '2', '5', '2'),
  ('2', '3', '5', '2'),
  ('3', '1', '5', '2'),
  ('4', '2', '5', '2'),
  ('5', '3', '5', '2'),
  ('6', '1', '5', '2'),
  ('7', '2', '5', '2'),
  ('8', '3', '5', '2'),
  ('9', '1', '5', '2'),
  ('10', '2', '5', '2');

INSERT INTO Cliente (email, telefono, dataregistrazione, codicefiscale) VALUES
  ('mario.rossi@test.it', NULL, '2024-01-01', 'RSSMRA80A01H501U'),
  ('francesco.esposito@test.it', '3331234567', '2026-05-16', 'SPSFNC82C10F205Z'),
  ('giulia.bianchi@test.it', '3330000001', '2025-01-12', 'BNCGLI90D45D612Y'),
  ('andrea.verdi@test.it', '3330000002', '2025-01-18', 'VRDNDR85E12F205K'),
  ('elena.neri@test.it', '3330000003', '2025-02-04', 'NRELNE92F50G224T'),
  ('luca.ferri@test.it', '3330000004', '2025-02-20', 'FRRLCU88L20H501V'),
  ('martina.gallo@test.it', '3330000005', '2025-03-02', 'GLLMTN95M41A944S'),
  ('paolo.romano@test.it', '3330000006', '2025-03-14', 'RMNPLA84P08L219D'),
  ('sara.conti@test.it', '3330000007', '2025-04-01', 'CNTSRA91R55F205X'),
  ('davide.moretti@test.it', '3330000008', '2025-04-16', 'MRTDVD86S30G224B'),
  ('admin@greenlog.test', '0288001001', '2025-01-10', '20000000001'),
  ('fleet@urbanmove.test', '0117002002', '2025-01-25', '20000000002'),
  ('operations@ecocargo.test', '0516003003', '2025-02-08', '20000000003'),
  ('delivery@cityfood.test', '0644004004', '2025-02-22', '20000000004'),
  ('mobility@smartdelivery.test', '0553005005', '2025-03-11', '20000000005'),
  ('logistica@freshmarket.test', '0499006006', '2025-03-25', '20000000006');

INSERT INTO ClienteCorporate (ragionesociale, partitaiva, livellocontratto, cliente) VALUES
  ('GreenLog S.r.l.', 'IT20000000001', 'premium', '20000000001'),
  ('UrbanMove Italia S.p.A.', 'IT20000000002', 'gold', '20000000002'),
  ('EcoCargo Nord S.r.l.', 'IT20000000003', 'silver', '20000000003'),
  ('CityFood Delivery S.r.l.', 'IT20000000004', 'base', '20000000004'),
  ('SmartDelivery Toscana S.r.l.', 'IT20000000005', 'gold', '20000000005'),
  ('FreshMarket Logistics S.r.l.', 'IT20000000006', 'silver', '20000000006');

INSERT INTO ClientePrivato (nome, cognome, patente, cliente) VALUES
  ('Mario', 'Rossi', 'PD12345', 'RSSMRA80A01H501U'),
  ('Francesco', 'Esposito', 'U1C111111X', 'SPSFNC82C10F205Z'),
  ('Giulia', 'Bianchi', 'PD900001', 'BNCGLI90D45D612Y'),
  ('Andrea', 'Verdi', 'PD900002', 'VRDNDR85E12F205K'),
  ('Elena', 'Neri', 'PD900003', 'NRELNE92F50G224T'),
  ('Luca', 'Ferri', 'PD900004', 'FRRLCU88L20H501V'),
  ('Martina', 'Gallo', 'PD900005', 'GLLMTN95M41A944S'),
  ('Paolo', 'Romano', 'PD900006', 'RMNPLA84P08L219D'),
  ('Sara', 'Conti', 'PD900007', 'CNTSRA91R55F205X'),
  ('Davide', 'Moretti', 'PD900008', 'MRTDVD86S30G224B');

INSERT INTO DipendenteCorporate (nome, cognome, reparto, clientecorporate, codicedipendente) VALUES
  ('Laura', 'Conti', 'Logistica', '20000000001', 'GL-001'),
  ('Marco', 'Rinaldi', 'Operations', '20000000001', 'GL-002'),
  ('Irene', 'Costa', 'Amministrazione', '20000000001', 'GL-003'),
  ('Sara', 'Ferrari', 'Fleet', '20000000002', 'UM-001'),
  ('Davide', 'Moretti', 'Operations', '20000000002', 'UM-002'),
  ('Alessio', 'Grassi', 'Logistica', '20000000002', 'UM-003'),
  ('Giulia', 'Romano', 'Magazzino', '20000000003', 'EC-001'),
  ('Andrea', 'Galli', 'Trasporti', '20000000003', 'EC-002'),
  ('Paolo', 'Marini', 'Delivery', '20000000004', 'CF-001'),
  ('Elena', 'Serra', 'Customer Care', '20000000004', 'CF-002'),
  ('Francesca', 'Lombardi', 'Operations', '20000000005', 'SD-001'),
  ('Matteo', 'Costa', 'Logistica', '20000000005', 'SD-002'),
  ('Chiara', 'Riva', 'Magazzino', '20000000006', 'FM-001'),
  ('Simone', 'Barbieri', 'Trasporti', '20000000006', 'FM-002');

INSERT INTO Tecnico (nome, cognome, specializzazione, matricola) VALUES
  ('Mario', 'Rossi', 'Meccanico Senior', 'TEC-001'),
  ('Luigi', 'Verdi', 'Diagnostica Batterie', 'TEC-002'),
  ('Anna', 'Bianchi', 'Elettronica di bordo', 'TEC-003'),
  ('Alessandro', 'Neri', 'Software e Connettività', 'TEC-004'),
  ('Giulia', 'Gialli', 'Riparazione Mezzi Leggeri (Scooter)', 'TEC-005');

INSERT INTO Certificazione (codicecertificazione, titolo, ambito) VALUES
  ('1', 'Alta Tensione EV', 'Sistemi Elettrici'),
  ('2', 'Diagnostica Batterie', 'Batterie'),
  ('3', 'Riparazione Motori EV', 'Motori'),
  ('4', 'Sistemi CCS Combo', 'Ricarica'),
  ('5', 'Manutenzione Scooter EV', 'Micromobilità'),
  ('6', 'Sicurezza Impianti', 'Sicurezza'),
  ('7', 'Firmware Veicoli', 'Software'),
  ('8', 'Telemetria EV', 'Elettronica'),
  ('9', 'Ricarica Rapida DC', 'Colonnine'),
  ('10', 'Gestione Flotte', 'Fleet Management');

INSERT INTO Abilitazione (certificazione, datarilascio, enterilascio, tecnico) VALUES
  ('1', '2024-03-15', 'CEI (Comitato Elettrotecnico Italiano)', 'TEC-001'),
  ('2', '2024-11-20', 'TÜV Rheinland', 'TEC-001'),
  ('5', '2025-01-10', 'Accademia della Bicicletta Milano', 'TEC-002'),
  ('2', '2023-05-14', 'TÜV Süd', 'TEC-003'),
  ('3', '2024-02-18', 'Anie Automazione', 'TEC-003'),
  ('4', '2025-04-02', 'Oracle IoT Academy', 'TEC-004'),
  ('5', '2024-06-22', 'Formazione Partner Piaggio', 'TEC-005'),
  ('3', '2025-02-11', 'CEI', 'TEC-005'),
  ('6', '2025-01-14', 'CEI', 'TEC-001'),
  ('9', '2025-02-10', 'TÜV Italia', 'TEC-001'),
  ('10', '2025-03-05', 'Fleet Management Academy', 'TEC-001'),
  ('2', '2025-01-20', 'TÜV Rheinland', 'TEC-002'),
  ('7', '2025-02-28', 'EV Software Academy', 'TEC-002'),
  ('8', '2025-03-18', 'Telemetria Italia', 'TEC-002'),
  ('1', '2025-01-30', 'CEI', 'TEC-003'),
  ('6', '2025-04-12', 'Sicurezza Impianti Italia', 'TEC-003'),
  ('9', '2025-05-09', 'Ricarica Rapida Academy', 'TEC-003'),
  ('7', '2025-02-04', 'Oracle IoT Academy', 'TEC-004'),
  ('8', '2025-03-11', 'Telemetria Italia', 'TEC-004'),
  ('10', '2025-04-21', 'Fleet Management Academy', 'TEC-004'),
  ('6', '2025-02-16', 'CEI', 'TEC-005'),
  ('9', '2025-04-04', 'TÜV Italia', 'TEC-005');

INSERT INTO AutoElettrica (veicolo, autonomiakm, capacitabatteriakwh, costoorario) VALUES
  ('102', '450', '75.00', '14.00'),
  ('103', '260', '42.00', '8.50'),
  ('104', '350', '62.00', '10.00'),
  ('105', '430', '77.40', '13.00'),
  ('106', '440', '77.40', '13.50'),
  ('107', '170', '26.80', '6.50'),
  ('108', '490', '80.70', '17.00'),
  ('109', '420', '76.60', '15.00'),
  ('110', '400', '66.50', '15.50'),
  ('111', '440', '78.00', '14.00'),
  ('112', '380', '58.00', '11.00'),
  ('113', '390', '64.00', '9.50'),
  ('114', '470', '88.00', '16.00'),
  ('115', '400', '75.00', '13.00'),
  ('116', '410', '93.40', '25.00');

INSERT INTO FurgoneElettrico (veicolo, autonomiakm, capacitacarico, costoorario) VALUES
  ('117', '280', '800.00', '17.00'),
  ('118', '330', '1000.00', '21.00'),
  ('119', '330', '1000.00', '20.00'),
  ('120', '400', '1500.00', '27.00'),
  ('121', '300', '600.00', '16.00'),
  ('122', '300', '1800.00', '25.00'),
  ('123', '410', '650.00', '19.50'),
  ('124', '280', '1200.00', '23.00'),
  ('125', '275', '800.00', '16.50'),
  ('126', '310', '900.00', '22.00'),
  ('127', '200', '1300.00', '24.00'),
  ('128', '330', '1000.00', '21.00'),
  ('129', '275', '750.00', '17.50'),
  ('130', '320', '1100.00', '22.50'),
  ('131', '330', '1000.00', '20.00');

INSERT INTO VeicoloLeggeroElettrico (veicolo, necessitacolonnina, costoorario, tipomezzo) VALUES
  ('132', 't', '3.50', 'Scooter'),
  ('133', 't', '5.00', 'Scooter'),
  ('134', 't', '4.50', 'Scooter'),
  ('135', 't', '4.00', 'Scooter'),
  ('136', 't', '4.20', 'Scooter'),
  ('137', 't', '7.00', 'Scooter'),
  ('138', 't', '4.50', 'Scooter'),
  ('139', 't', '3.80', 'Scooter'),
  ('140', 't', '3.20', 'Scooter'),
  ('141', 't', '3.60', 'Scooter'),
  ('142', 'f', '2.50', 'e-bike'),
  ('143', 'f', '2.80', 'e-bike');

INSERT INTO Batteria (serialebatteria, capacita, cicliricarica, statobatteria, veicolo, percentualebatteria) VALUES
  ('BAT-CAR-001', '75.00', '21', 'Disponibile', '102', '76'),
  ('BAT-CAR-002', '42.00', '27', 'Disponibile', '103', '77'),
  ('BAT-CAR-003', '62.00', '33', 'Disponibile', '104', '78'),
  ('BAT-CAR-004', '77.40', '39', 'Disponibile', '105', '79'),
  ('BAT-CAR-005', '77.40', '45', 'Disponibile', '106', '80'),
  ('BAT-CAR-006', '26.80', '51', 'Disponibile', '107', '81'),
  ('BAT-CAR-007', '80.70', '57', 'Disponibile', '108', '82'),
  ('BAT-CAR-008', '76.60', '63', 'Disponibile', '109', '83'),
  ('BAT-CAR-009', '66.50', '69', 'Disponibile', '110', '84'),
  ('BAT-CAR-010', '78.00', '75', 'Disponibile', '111', '85'),
  ('BAT-CAR-011', '58.00', '81', 'In Uso', '112', '42'),
  ('BAT-CAR-012', '64.00', '87', 'In Uso', '113', '49'),
  ('BAT-CAR-013', '88.00', '93', 'In Uso', '114', '56'),
  ('BAT-CAR-014', '75.00', '99', 'In Carica', '115', '22'),
  ('BAT-CAR-015', '93.40', '105', 'In Manutenzione', '116', '45'),
  ('BAT-VAN-016', '50.00', '99', 'Disponibile', '117', '96'),
  ('BAT-VAN-017', '75.00', '103', 'Disponibile', '118', '97'),
  ('BAT-VAN-018', '75.00', '107', 'Disponibile', '119', '98'),
  ('BAT-VAN-019', '113.00', '111', 'Disponibile', '120', '99'),
  ('BAT-VAN-020', '45.00', '115', 'Disponibile', '121', '80'),
  ('BAT-VAN-021', '74.00', '119', 'Disponibile', '122', '81'),
  ('BAT-VAN-022', '77.00', '123', 'Disponibile', '123', '82'),
  ('BAT-VAN-023', '79.00', '127', 'Disponibile', '124', '83'),
  ('BAT-VAN-024', '50.00', '131', 'Disponibile', '125', '84'),
  ('BAT-VAN-025', '60.00', '135', 'Disponibile', '126', '85'),
  ('BAT-VAN-026', '52.00', '139', 'In Uso', '127', '58'),
  ('BAT-VAN-027', '75.00', '143', 'In Uso', '128', '61'),
  ('BAT-VAN-028', '50.00', '147', 'In Uso', '129', '64'),
  ('BAT-VAN-029', '64.00', '151', 'In Carica', '130', '24'),
  ('BAT-VAN-030', '75.00', '155', 'In Carica', '131', '15'),
  ('BAT-SCOO-031', '2.30', '72', 'Disponibile', '132', '74'),
  ('BAT-SCOO-032', '4.20', '74', 'Disponibile', '133', '78'),
  ('BAT-SCOO-033', '5.60', '76', 'Disponibile', '134', '82'),
  ('BAT-SCOO-034', '4.20', '78', 'Disponibile', '135', '86'),
  ('BAT-SCOO-035', '5.40', '80', 'Disponibile', '136', '90'),
  ('BAT-SCOO-036', '8.90', '82', 'In Uso', '137', '39'),
  ('BAT-SCOO-037', '5.60', '84', 'In Uso', '138', '48'),
  ('BAT-SCOO-038', '2.80', '86', 'In Carica', '139', '40'),
  ('BAT-SCOO-039', '2.40', '88', 'In Carica', '140', '40'),
  ('BAT-SCOO-040', '2.60', '90', 'In Manutenzione', '141', '55'),
  ('BAT-EBIKE-041', '0.75', '44', 'Disponibile', '142', '88'),
  ('BAT-EBIKE-042', '0.65', '39', 'Disponibile', '143', '91');


INSERT INTO Manutenzione (dataoraintervento, tipointervento, costo, esito, veicolo, tecnico) VALUES
  ('2026-05-20', 'Sostituzione Celle Batteria', '450.00', 'In Corso', '116', 'TEC-002'),
  ('2026-05-20', 'Riparazione Sistema Frenante', '320.50', 'In Corso', '141', 'TEC-003'),
  ('2026-06-01', 'ordinaria', '95.00', 'Completata', '102', 'TEC-001'),
  ('2026-06-02', 'software', '120.00', 'Completata', '103', 'TEC-004'),
  ('2026-06-03', 'hardware', '280.00', 'Completata', '104', 'TEC-003'),
  ('2026-06-04', 'ordinaria', '85.00', 'Completata', '105', 'TEC-001'),
  ('2026-06-05', 'straordinaria', '520.00', 'Completata', '106', 'TEC-002'),
  ('2026-06-06', 'hardware', '310.00', 'Completata', '107', 'TEC-003'),
  ('2026-06-07', 'software', '140.00', 'Completata', '108', 'TEC-004'),
  ('2026-06-08', 'ordinaria', '75.00', 'Completata', '109', 'TEC-001'),
  ('2026-06-09', 'hardware', '190.00', 'Completata', '110', 'TEC-003'),
  ('2026-06-10', 'straordinaria', '610.00', 'Completata', '111', 'TEC-002'),
  ('2026-06-11', 'ordinaria', '110.00', 'Completata', '117', 'TEC-001'),
  ('2026-06-12', 'hardware', '340.00', 'Completata', '118', 'TEC-003'),
  ('2026-06-13', 'software', '155.00', 'Completata', '119', 'TEC-004'),
  ('2026-06-14', 'straordinaria', '720.00', 'Completata', '120', 'TEC-002'),
  ('2026-06-15', 'ordinaria', '100.00', 'Completata', '121', 'TEC-001'),
  ('2026-06-16', 'hardware', '360.00', 'Completata', '122', 'TEC-003'),
  ('2026-06-17', 'software', '180.00', 'Completata', '123', 'TEC-004'),
  ('2026-06-18', 'ordinaria', '105.00', 'Completata', '124', 'TEC-001'),
  ('2026-06-19', 'straordinaria', '650.00', 'Completata', '125', 'TEC-002'),
  ('2026-06-20', 'hardware', '295.00', 'Completata', '126', 'TEC-003'),
  ('2026-06-21', 'ordinaria', '70.00', 'Completata', '132', 'TEC-005'),
  ('2026-06-22', 'software', '95.00', 'Completata', '133', 'TEC-004'),
  ('2026-06-23', 'hardware', '160.00', 'Completata', '134', 'TEC-005'),
  ('2026-06-24', 'ordinaria', '65.00', 'Completata', '135', 'TEC-005'),
  ('2026-06-25', 'straordinaria', '260.00', 'Completata', '136', 'TEC-005'),
  ('2026-06-26', 'software', '130.00', 'Completata', '139', 'TEC-004'),
  ('2026-06-27', 'hardware', '210.00', 'Completata', '140', 'TEC-005'),
  ('2026-06-28', 'ordinaria', '80.00', 'Completata', '141', 'TEC-005');


INSERT INTO Noleggio (codicenoleggio, dataorainizio, dataorafine, costototale, kmpercorsi, veicolo, puntoinizio, puntofine, hubinizio, stazioneinizio, hubfine, stazionefine, cliente) VALUES
    ('1', '2026-05-20 14:45:10', '2026-05-20 16:45:10', '22.00', '35', '112', '3', '3', '1', '1', '1', '1', 'BNCGLI90D45D612Y'),
    ('2', '2026-05-20 14:45:10', '2026-05-20 17:45:10', '28.50', '35', '113', '3', '9', '1', '1', '1', '3', 'RSSMRA80A01H501U'),
    ('3', '2026-05-20 14:45:10', '2026-05-20 16:45:10', '32.00', '35', '114', '6', '6', '1', '1', '1', '1', 'VRDNDR85E12F205K'),
    ('4', '2026-05-20 14:45:10', '2026-05-20 17:45:10', '72.00', '35', '127', '4', '10', '1', '1', '1', '3', 'RSSMRA80A01H501U'),
    ('5', '2026-05-20 14:45:10', '2026-05-20 16:45:10', '42.00', '35', '128', '7', '4', '1', '1', '1', '1', 'NRELNE92F50G224T'),
    ('6', '2026-05-20 14:45:10', '2026-05-20 17:45:10', '52.50', '35', '129', '7', '4', '1', '1', '1', '3', 'RSSMRA80A01H501U'),
    ('7', '2026-05-20 14:45:10', NULL, NULL, NULL, '137', '8', NULL, '1', '1', NULL, NULL, 'SPSFNC82C10F205Z'),
    ('8', '2026-05-20 14:45:10', NULL, NULL, NULL, '138', '8', NULL, '1', '1', NULL, NULL, 'RSSMRA80A01H501U'),
    ('9', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '28.00', '32', '102', '3', '6', '1', '1', '1', '1', 'RSSMRA80A01H501U'),
    ('10', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '42.00', '51', '102', '3', '6', '1', '1', '1', '1', 'RSSMRA80A01H501U'),
    ('11', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '34.00', '72', '103', '6', '9', '1', '1', '1', '1', 'RSSMRA80A01H501U'),
    ('12', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '8.50', '19', '103', '6', '9', '1', '1', '1', '1', 'RSSMRA80A01H501U'),
    ('13', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '20.00', '40', '104', '6', '9', '1', '1', '1', '1', 'RSSMRA80A01H501U'),
    ('14', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '30.00', '63', '104', '9', '9', '1', '1', '1', '1', 'RSSMRA80A01H501U'),
    ('15', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '52.00', '88', '105', '9', '3', '1', '1', '1', '2', 'RSSMRA80A01H501U'),
    ('16', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '13.00', '23', '105', '9', '3', '1', '1', '1', '2', 'RSSMRA80A01H501U'),
    ('17', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '27.00', '48', '106', '9', '3', '1', '1', '1', '2', 'RSSMRA80A01H501U'),
    ('18', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '40.50', '75', '106', '3', '6', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('19', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '26.00', '104', '107', '3', '6', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('20', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '6.50', '27', '107', '3', '6', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('21', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '34.00', '56', '108', '6', '9', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('22', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '51.00', '87', '108', '6', '9', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('23', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '60.00', '120', '109', '6', '9', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('24', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '15.00', '31', '109', '9', '9', '1', '2', '1', '2', 'RSSMRA80A01H501U'),
    ('25', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '31.00', '64', '110', '9', '3', '1', '2', '1', '3', 'RSSMRA80A01H501U'),
    ('26', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '46.50', '99', '110', '9', '3', '1', '2', '1', '3', 'RSSMRA80A01H501U'),
    ('27', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '56.00', '136', '111', '9', '3', '1', '2', '1', '3', 'RSSMRA80A01H501U'),
    ('28', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '14.00', '15', '111', '3', '6', '1', '3', '1', '3', 'RSSMRA80A01H501U'),
    ('29', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '22.00', '32', '112', '3', '6', '1', '3', '1', '3', 'RSSMRA80A01H501U'),
    ('30', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '33.00', '51', '112', '3', '6', '1', '3', '1', '3', 'RSSMRA80A01H501U'),
    ('31', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '38.00', '72', '113', '6', '9', '1', '3', '1', '3', 'RSSMRA80A01H501U'),
    ('32', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '9.50', '19', '113', '6', '9', '1', '3', '1', '3', 'RSSMRA80A01H501U'),
    ('33', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '32.00', '40', '114', '6', '9', '1', '3', '1', '3', 'BNCGLI90D45D612Y'),
    ('34', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '48.00', '63', '114', '9', '9', '1', '3', '1', '3', 'BNCGLI90D45D612Y'),
    ('35', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '52.00', '88', '115', '9', '3', '1', '3', '2', '1', 'BNCGLI90D45D612Y'),
    ('36', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '13.00', '23', '115', '9', '3', '1', '3', '2', '1', 'BNCGLI90D45D612Y'),
    ('37', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '34.00', '48', '117', '10', '4', '1', '3', '2', '1', 'BNCGLI90D45D612Y'),
    ('38', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '51.00', '75', '117', '1', '4', '2', '1', '2', '1', 'BNCGLI90D45D612Y'),
    ('39', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '84.00', '104', '118', '1', '4', '2', '1', '2', '1', 'VRDNDR85E12F205K'),
    ('40', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '21.00', '27', '118', '4', '7', '2', '1', '2', '1', 'VRDNDR85E12F205K'),
    ('41', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '40.00', '56', '119', '4', '7', '2', '1', '2', '1', 'VRDNDR85E12F205K'),
    ('42', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '60.00', '87', '119', '4', '7', '2', '1', '2', '1', 'VRDNDR85E12F205K'),
    ('43', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '108.00', '120', '120', '7', '10', '2', '1', '2', '1', 'VRDNDR85E12F205K'),
    ('44', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '27.00', '31', '120', '7', '10', '2', '1', '2', '1', 'VRDNDR85E12F205K'),
    ('45', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '32.00', '64', '121', '7', '1', '2', '1', '2', '2', 'RMNPLA84P08L219D'),
    ('46', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '48.00', '99', '121', '10', '1', '2', '1', '2', '2', 'RMNPLA84P08L219D'),
    ('47', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '100.00', '136', '122', '10', '4', '2', '1', '2', '2', 'RMNPLA84P08L219D'),
    ('48', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '25.00', '15', '122', '1', '4', '2', '2', '2', '2', 'RMNPLA84P08L219D'),
    ('49', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '39.00', '32', '123', '1', '4', '2', '2', '2', '2', 'RMNPLA84P08L219D'),
    ('50', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '58.50', '51', '123', '4', '7', '2', '2', '2', '2', 'RMNPLA84P08L219D'),
    ('51', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '92.00', '72', '124', '4', '7', '2', '2', '2', '2', 'CNTSRA91R55F205X'),
    ('52', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '23.00', '19', '124', '4', '7', '2', '2', '2', '2', 'CNTSRA91R55F205X'),
    ('53', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '33.00', '40', '125', '7', '10', '2', '2', '2', '2', 'CNTSRA91R55F205X'),
    ('54', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '49.50', '63', '125', '7', '10', '2', '2', '2', '2', 'CNTSRA91R55F205X'),
    ('55', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '88.00', '88', '126', '7', '1', '2', '2', '3', '1', 'CNTSRA91R55F205X'),
    ('56', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '22.00', '23', '126', '10', '1', '2', '2', '3', '1', 'CNTSRA91R55F205X'),
    ('57', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '48.00', '48', '127', '10', '4', '2', '2', '3', '1', 'MRTDVD86S30G224B'),
    ('58', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '72.00', '75', '127', '1', '4', '3', '1', '3', '1', 'MRTDVD86S30G224B'),
    ('59', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '84.00', '104', '128', '1', '4', '3', '1', '3', '1', 'MRTDVD86S30G224B'),
    ('60', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '21.00', '27', '128', '4', '7', '3', '1', '3', '1', 'MRTDVD86S30G224B'),
    ('61', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '35.00', '56', '129', '4', '7', '3', '1', '3', '1', 'MRTDVD86S30G224B'),
    ('62', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '52.50', '87', '129', '4', '7', '3', '1', '3', '1', 'MRTDVD86S30G224B'),
    ('63', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '76.50', '120', '130', '7', '10', '3', '1', '3', '1', '20000000001'),
    ('64', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '19.13', '31', '130', '7', '10', '3', '1', '3', '1', '20000000001'),
    ('65', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '34.00', '64', '131', '7', '1', '3', '1', '3', '2', '20000000001'),
    ('66', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '51.00', '99', '131', '10', '1', '3', '1', '3', '2', '20000000001'),
    ('67', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '12.60', '136', '132', '8', '2', '3', '1', '3', '2', '20000000002'),
    ('68', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '3.15', '15', '132', '2', '5', '3', '2', '3', '2', '20000000002'),
    ('69', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '9.00', '32', '133', '2', '5', '3', '2', '3', '2', '20000000002'),
    ('70', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '13.50', '51', '133', '2', '5', '3', '2', '3', '2', '20000000002'),
    ('71', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '17.10', '72', '134', '5', '8', '3', '2', '3', '2', '20000000003'),
    ('72', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '4.28', '19', '134', '5', '8', '3', '2', '3', '2', '20000000003'),
    ('73', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '7.60', '40', '135', '5', '8', '3', '2', '3', '2', '20000000003'),
    ('74', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '11.40', '63', '135', '8', '8', '3', '2', '3', '2', '20000000003'),
    ('75', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '16.80', '88', '136', '8', '2', '3', '2', '4', '1', '20000000004'),
    ('76', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '4.20', '23', '136', '8', '2', '3', '2', '4', '1', '20000000004'),
    ('77', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '14.00', '48', '137', '8', '2', '3', '2', '4', '1', '20000000004'),
    ('78', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '21.00', '75', '137', '2', '5', '4', '1', '4', '1', '20000000004'),
    ('79', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '16.20', '104', '138', '2', '5', '4', '1', '4', '1', '20000000005'),
    ('80', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '4.05', '27', '138', '2', '5', '4', '1', '4', '1', '20000000005'),
    ('81', '2026-05-18 14:45:10', '2026-05-18 16:45:10', '6.84', '56', '139', '5', '8', '4', '1', '4', '1', '20000000005'),
    ('82', '2026-05-16 13:45:10', '2026-05-16 16:45:10', '10.26', '87', '139', '5', '8', '4', '1', '4', '1', '20000000005'),
    ('83', '2026-05-18 12:45:10', '2026-05-18 16:45:10', '12.16', '120', '140', '5', '8', '4', '1', '4', '1', '20000000006'),
    ('84', '2026-05-16 15:45:10', '2026-05-16 16:45:10', '3.04', '31', '140', '8', '8', '4', '1', '4', '1', '20000000006'),
    ('2041', '2026-04-20 08:00:00', NULL, NULL, NULL, '109', '3', NULL, '1', '1', NULL, NULL, 'NRELNE92F50G224T'),
    ('2042', '2026-04-20 08:15:00', NULL, NULL, NULL, '122', '1', NULL, '2', '1', NULL, NULL, 'FRRLCU88L20H501V'),
    ('2043', '2026-04-20 08:30:00', NULL, NULL, NULL, '135', '2', NULL, '3', '1', NULL, NULL, 'GLLMTN95M41A944S'),
    ('2044', '2026-04-20 09:00:00', NULL, NULL, NULL, '110', '6', NULL, '4', '1', NULL, NULL, '20000000002'),
    ('2045', '2026-04-20 09:30:00', NULL, NULL, NULL, '123', '4', NULL, '5', '1', NULL, NULL, '20000000003'),
    ('2046', '2026-04-20 10:00:00', NULL, NULL, NULL, '136', '5', NULL, '5', '2', NULL, NULL, '20000000004'),
    ('2047', '2026-04-21 09:00:00', '2026-04-21 11:00:00', '5.00', '12', '142', '2', '5', '3', '1', '3', '1', 'RMNPLA84P08L219D'),
    ('2048', '2026-04-22 15:30:00', '2026-04-22 18:30:00', '8.40', '18', '143', '5', '8', '5', '2', '5', '2', 'CNTSRA91R55F205X');


INSERT INTO Ricevuta (codicericevuta, noleggio, dataemissione, metodopagamento) VALUES
  ('1', '9', '2026-05-18 16:46:10', 'PayPal'),
  ('2', '10', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('3', '11', '2026-05-18 16:46:10', 'PayPal'),
  ('4', '12', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('5', '13', '2026-05-18 16:46:10', 'PayPal'),
  ('6', '14', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('7', '15', '2026-05-18 16:46:10', 'PayPal'),
  ('8', '16', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('9', '17', '2026-05-18 16:46:10', 'PayPal'),
  ('10', '18', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('11', '19', '2026-05-18 16:46:10', 'PayPal'),
  ('12', '20', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('13', '21', '2026-05-18 16:46:10', 'PayPal'),
  ('14', '22', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('15', '23', '2026-05-18 16:46:10', 'PayPal'),
  ('16', '24', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('17', '25', '2026-05-18 16:46:10', 'PayPal'),
  ('18', '26', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('19', '27', '2026-05-18 16:46:10', 'PayPal'),
  ('20', '28', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('21', '29', '2026-05-18 16:46:10', 'PayPal'),
  ('22', '30', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('23', '31', '2026-05-18 16:46:10', 'PayPal'),
  ('24', '32', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('25', '33', '2026-05-18 16:46:10', 'PayPal'),
  ('26', '34', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('27', '35', '2026-05-18 16:46:10', 'PayPal'),
  ('28', '36', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('29', '37', '2026-05-18 16:46:10', 'PayPal'),
  ('30', '38', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('31', '39', '2026-05-18 16:46:10', 'PayPal'),
  ('32', '40', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('33', '41', '2026-05-18 16:46:10', 'PayPal'),
  ('34', '42', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('35', '43', '2026-05-18 16:46:10', 'PayPal'),
  ('36', '44', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('37', '45', '2026-05-18 16:46:10', 'PayPal'),
  ('38', '46', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('39', '47', '2026-05-18 16:46:10', 'PayPal'),
  ('40', '48', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('41', '49', '2026-05-18 16:46:10', 'PayPal'),
  ('42', '50', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('43', '51', '2026-05-18 16:46:10', 'PayPal'),
  ('44', '52', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('45', '53', '2026-05-18 16:46:10', 'PayPal'),
  ('46', '54', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('47', '55', '2026-05-18 16:46:10', 'PayPal'),
  ('48', '56', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('49', '57', '2026-05-18 16:46:10', 'PayPal'),
  ('50', '58', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('51', '59', '2026-05-18 16:46:10', 'PayPal'),
  ('52', '60', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('53', '61', '2026-05-18 16:46:10', 'PayPal'),
  ('54', '62', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('55', '63', '2026-05-18 16:46:10', 'PayPal'),
  ('56', '64', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('57', '65', '2026-05-18 16:46:10', 'PayPal'),
  ('58', '66', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('59', '67', '2026-05-18 16:46:10', 'PayPal'),
  ('60', '68', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('61', '69', '2026-05-18 16:46:10', 'PayPal'),
  ('62', '70', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('63', '71', '2026-05-18 16:46:10', 'PayPal'),
  ('64', '72', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('65', '73', '2026-05-18 16:46:10', 'PayPal'),
  ('66', '74', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('67', '75', '2026-05-18 16:46:10', 'PayPal'),
  ('68', '76', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('69', '77', '2026-05-18 16:46:10', 'PayPal'),
  ('70', '78', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('71', '79', '2026-05-18 16:46:10', 'PayPal'),
  ('72', '80', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('73', '81', '2026-05-18 16:46:10', 'PayPal'),
  ('74', '82', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('75', '83', '2026-05-18 16:46:10', 'PayPal'),
  ('76', '84', '2026-05-16 16:46:10', 'Carta di Credito'),
  ('77', '2047', '2026-04-21 11:01:00', 'Carta di Credito'),
  ('78', '2048', '2026-04-22 18:31:00', 'PayPal'),
  ('79', '1', '2026-05-20 16:46:10', 'Carta di Credito'),
  ('80', '2', '2026-05-20 17:46:10', 'Carta di Credito'),
  ('81', '3', '2026-05-20 16:46:10', 'PayPal'),
  ('82', '4', '2026-05-20 17:46:10', 'Carta di Credito'),
  ('83', '5', '2026-05-20 16:46:10', 'Bonifico Bancario'),
  ('84', '6', '2026-05-20 17:46:10', 'Carta di Credito');



-- ALLINEAMENTO SEQUENZE DOPO POPOLAMENTO --

SELECT setval('veicolo_idveicolo_seq', COALESCE((SELECT MAX(serialeveicolo) FROM Veicolo), 1), true);
SELECT setval('hublogistico_idhub_seq', COALESCE((SELECT MAX(codicehub) FROM HubLogistico), 1), true);
SELECT setval('certificazione_codicecertificazione_seq', COALESCE((SELECT MAX(codicecertificazione) FROM Certificazione), 1), true);
SELECT setval('noleggio_idnoleggio_seq', COALESCE((SELECT MAX(codicenoleggio) FROM Noleggio), 1), true);
SELECT setval('ricevuta_id_ricevuta_seq', COALESCE((SELECT MAX(codicericevuta) FROM Ricevuta), 1), true);


-- FUNZIONI E TRIGGER --

CREATE OR REPLACE FUNCTION aggiorna_km_veicolo()
RETURNS trigger AS $$
BEGIN
    IF OLD.kmpercorsi IS NULL AND NEW.kmpercorsi IS NOT NULL THEN
        UPDATE Veicolo
        SET kmtotali = kmtotali + NEW.kmpercorsi
        WHERE serialeveicolo = NEW.veicolo;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_costo_orario_veicolo(p_veicolo INTEGER)
RETURNS NUMERIC AS $$
DECLARE
    v_costo NUMERIC(8,2);
BEGIN
    SELECT costoorario
    INTO v_costo
    FROM AutoElettrica
    WHERE veicolo = p_veicolo;

    IF FOUND THEN
        RETURN v_costo;
    END IF;

    SELECT costoorario
    INTO v_costo
    FROM FurgoneElettrico
    WHERE veicolo = p_veicolo;

    IF FOUND THEN
        RETURN v_costo;
    END IF;

    SELECT costoorario
    INTO v_costo
    FROM VeicoloLeggeroElettrico
    WHERE veicolo = p_veicolo;

    IF FOUND THEN
        RETURN v_costo;
    END IF;

    RAISE EXCEPTION 'Il veicolo % non appartiene ad alcuna tipologia.', p_veicolo;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_fattore_sconto_cliente(p_cliente VARCHAR)
RETURNS NUMERIC AS $$
DECLARE
    v_livello VARCHAR(30);
BEGIN
    SELECT livellocontratto
    INTO v_livello
    FROM ClienteCorporate
    WHERE cliente = p_cliente;

    IF NOT FOUND THEN
        RETURN 1.00;
    END IF;

    CASE LOWER(v_livello)
        WHEN 'base' THEN RETURN 1.00;
        WHEN 'silver' THEN RETURN 0.95;
        WHEN 'gold' THEN RETURN 0.90;
        WHEN 'premium' THEN RETURN 0.85;
        ELSE RETURN 1.00;
    END CASE;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION calcola_costo_noleggio()
RETURNS trigger AS $$
DECLARE
    v_durata_ore NUMERIC;
    v_costo_orario NUMERIC(8,2);
    v_fattore_sconto NUMERIC;
BEGIN
    IF NEW.dataorafine IS NOT NULL AND OLD.dataorafine IS NULL THEN
        v_durata_ore := EXTRACT(EPOCH FROM (NEW.dataorafine - NEW.dataorainizio)) / 3600.0;

        IF v_durata_ore <= 0 THEN
            RAISE EXCEPTION 'La durata del noleggio deve essere positiva.';
        END IF;

        v_costo_orario := get_costo_orario_veicolo(NEW.veicolo);
        v_fattore_sconto := get_fattore_sconto_cliente(NEW.cliente);

        NEW.costototale := ROUND(v_durata_ore * v_costo_orario * v_fattore_sconto, 2);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_limiti_e_connettori_noleggio()
RETURNS trigger AS $$
DECLARE
    v_noleggi_attivi INT;
BEGIN
    SELECT COUNT(*)
    INTO v_noleggi_attivi
    FROM Noleggio
    WHERE cliente = NEW.cliente AND dataorafine IS NULL AND codicenoleggio <> COALESCE(NEW.codicenoleggio, -1);

    IF v_noleggi_attivi > 0 THEN
        RAISE EXCEPTION 'Il cliente ha già un noleggio attivo in corso!';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_punto_libero()
RETURNS trigger AS $$
DECLARE
    v_punto_occupato INT;
BEGIN
    IF NEW.puntofine IS NOT NULL AND NEW.hubfine IS NOT NULL AND NEW.stazionefine IS NOT NULL THEN
        SELECT COUNT(*)
        INTO v_punto_occupato
        FROM Noleggio
        WHERE hubfine = NEW.hubfine AND stazionefine = NEW.stazionefine AND puntofine = NEW.puntofine AND dataorafine = NEW.dataorafine AND codicenoleggio <> COALESCE(NEW.codicenoleggio, -1);

        IF v_punto_occupato > 0 THEN
            RAISE EXCEPTION 'Operazione rifiutata: il punto di accesso selezionato è già occupato.';
        END IF;

    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION check_veicolo_disponibile()
RETURNS trigger AS $$
DECLARE
    v_noleggi_veicolo INT;
BEGIN
    SELECT COUNT(*)
    INTO v_noleggi_veicolo
    FROM Noleggio
    WHERE veicolo = NEW.veicolo AND dataorafine IS NULL AND codicenoleggio <> COALESCE(NEW.codicenoleggio, -1);

    IF v_noleggi_veicolo > 0 THEN
        RAISE EXCEPTION 'Operazione rifiutata: il veicolo con seriale % è già in uso in un altro noleggio attivo.', NEW.veicolo;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION crea_batteria_automatica()
RETURNS trigger AS $$
DECLARE
    v_capacita NUMERIC(6,2);
    v_targa VARCHAR(20);
BEGIN
    SELECT targa
    INTO v_targa
    FROM Veicolo
    WHERE serialeveicolo = NEW.veicolo;

    IF TG_TABLE_NAME = 'autoelettrica' THEN
        v_capacita := 50.00;
    ELSIF TG_TABLE_NAME = 'furgoneelettrico' THEN
        v_capacita := 75.00;
    ELSIF TG_TABLE_NAME = 'veicololeggeroelettrico' THEN
        v_capacita := 2.80;
    ELSE
        v_capacita := 10.00;
    END IF;

    INSERT INTO Batteria (serialebatteria, capacita, cicliricarica, statobatteria, veicolo, percentualebatteria)
    VALUES ('BATT-' || COALESCE(v_targa, NEW.veicolo::text), v_capacita, 0, 'Disponibile', NEW.veicolo, 100)
    ON CONFLICT (veicolo) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION genera_ricevuta_automatica()
RETURNS trigger AS $$
BEGIN
    IF NEW.dataorafine IS NOT NULL AND OLD.dataorafine IS NULL THEN
        INSERT INTO Ricevuta (codicericevuta, noleggio, dataemissione, metodopagamento)
        VALUES (nextval('ricevuta_id_ricevuta_seq'), NEW.codicenoleggio, NEW.dataorafine + INTERVAL '1 minute', 'Carta di Credito')
        ON CONFLICT (noleggio) DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION verifica_coerenza_ricevuta()
RETURNS trigger AS $$
DECLARE
    v_data_fine_noleggio TIMESTAMP;
BEGIN
    SELECT dataorafine
    INTO v_data_fine_noleggio
    FROM Noleggio
    WHERE codicenoleggio = NEW.noleggio;

    IF v_data_fine_noleggio IS NULL THEN
        RAISE EXCEPTION 'Operazione rifiutata: impossibile emettere una ricevuta per un noleggio non ancora concluso.';
    END IF;

    IF DATE_TRUNC('second', NEW.dataemissione) < DATE_TRUNC('second', v_data_fine_noleggio) THEN
        RAISE EXCEPTION 'Operazione rifiutata: la data di emissione della ricevuta non può precedere la fine del noleggio.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_tipo_connettore_veicolo(p_veicolo INTEGER)
RETURNS VARCHAR AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM AutoElettrica WHERE veicolo = p_veicolo) THEN
        RETURN '1';
    END IF;

    IF EXISTS (SELECT 1 FROM FurgoneElettrico WHERE veicolo = p_veicolo) THEN
        RETURN '2';
    END IF;

    IF EXISTS (SELECT 1 FROM VeicoloLeggeroElettrico WHERE veicolo = p_veicolo) THEN
        RETURN '3';
    END IF;

    RAISE EXCEPTION 'Il veicolo % non appartiene ad alcuna tipologia.', p_veicolo;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION verifica_compatibilita_connettore()
RETURNS TRIGGER AS $$
DECLARE
    v_tipo_richiesto VARCHAR(30);
    v_tipo_inizio VARCHAR(30);
    v_tipo_fine VARCHAR(30);
BEGIN
    v_tipo_richiesto := get_tipo_connettore_veicolo(NEW.veicolo);

    SELECT tipoconnettore
    INTO v_tipo_inizio
    FROM PuntoAccesso
    WHERE codicehub = NEW.hubinizio AND numerostazione = NEW.stazioneinizio AND numeropunto = NEW.puntoinizio;

    IF v_tipo_inizio IS NULL THEN
        RAISE EXCEPTION 'Punto iniziale inesistente: Hub %, Stazione %, Punto %.', NEW.hubinizio, NEW.stazioneinizio, NEW.puntoinizio;
    END IF;

    IF v_tipo_inizio <> v_tipo_richiesto THEN
        RAISE EXCEPTION 'Punto iniziale incompatibile con il veicolo %. Tipo richiesto %, trovato %.', NEW.veicolo, v_tipo_richiesto, v_tipo_inizio;
    END IF;

    IF NEW.hubfine IS NOT NULL AND NEW.stazionefine IS NOT NULL AND NEW.puntofine IS NOT NULL THEN

        SELECT tipoconnettore
        INTO v_tipo_fine
        FROM PuntoAccesso
        WHERE codicehub = NEW.hubfine AND numerostazione = NEW.stazionefine AND numeropunto = NEW.puntofine;

        IF v_tipo_fine IS NULL THEN
            RAISE EXCEPTION 'Punto finale inesistente: Hub %, Stazione %, Punto %.', NEW.hubfine, NEW.stazionefine, NEW.puntofine;
        END IF;

        IF v_tipo_fine <> v_tipo_richiesto THEN
            RAISE EXCEPTION 'Punto finale incompatibile con il veicolo %. Tipo richiesto %, trovato %.', NEW.veicolo, v_tipo_richiesto, v_tipo_fine;
        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- CREAZIONE TRIGGER --

CREATE TRIGGER trg_aggiorna_km_fine_noleggio
BEFORE UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION aggiorna_km_veicolo();

CREATE TRIGGER trg_calcola_costo
BEFORE UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION calcola_costo_noleggio();

CREATE TRIGGER trg_check_limiti_e_connettori
BEFORE INSERT OR UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION check_limiti_e_connettori_noleggio();

CREATE TRIGGER trg_punto_occupato
BEFORE INSERT OR UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION check_punto_libero();

CREATE TRIGGER trg_veicolo_occupato
BEFORE INSERT OR UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION check_veicolo_disponibile();

CREATE TRIGGER trg_controllo_vincoli_ricevuta
BEFORE INSERT OR UPDATE ON Ricevuta
FOR EACH ROW
EXECUTE FUNCTION verifica_coerenza_ricevuta();

CREATE TRIGGER trg_auto_crea_batt
AFTER INSERT ON AutoElettrica
FOR EACH ROW
EXECUTE FUNCTION crea_batteria_automatica();

CREATE TRIGGER trg_furgone_crea_batt
AFTER INSERT ON FurgoneElettrico
FOR EACH ROW
EXECUTE FUNCTION crea_batteria_automatica();

CREATE TRIGGER trg_scooter_crea_batt
AFTER INSERT ON VeicoloLeggeroElettrico
FOR EACH ROW
EXECUTE FUNCTION crea_batteria_automatica();

CREATE TRIGGER trg_noleggio_chiuso_genera_ricevuta
AFTER UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION genera_ricevuta_automatica();

CREATE TRIGGER trg_verifica_connettore
BEFORE INSERT OR UPDATE ON Noleggio
FOR EACH ROW
EXECUTE FUNCTION verifica_compatibilita_connettore();


--  CREAZIONE INDICI --

CREATE INDEX idx_manutenzione_veicolo
ON Manutenzione USING btree (veicolo);

CREATE INDEX idx_noleggio_cliente
ON Noleggio USING btree (cliente);

CREATE INDEX idx_noleggio_date
ON Noleggio USING btree (dataorainizio, dataorafine);

CREATE INDEX idx_noleggio_veicolo
ON Noleggio USING btree (veicolo);

CREATE INDEX idx_veicolo_stato
ON Veicolo USING btree (statooperativo);


-- DEFINIZIONI QUERY --

-- Query 1 - Performance economiche e di utilizzo per marca e modello
SELECT V.marca, V.modello, COUNT(N.codicenoleggio) AS NumeroNoleggiTotali,
       SUM(N.costototale) AS RicavoComplessivo, SUM(N.kmpercorsi) AS KmTotaliPercorsi
FROM Veicolo V JOIN Noleggio N ON V.serialeveicolo = N.veicolo
WHERE N.dataorafine IS NOT NULL
GROUP BY V.marca, V.modello
ORDER BY RicavoComplessivo DESC;


-- Query 2 - Clienti privati con spesa superiore a 100 euro
SELECT CP.nome, CP.cognome, CP.cliente AS CodiceFiscale,
       COUNT(N.codicenoleggio) AS NumeroNoleggi,
       SUM(N.costototale) AS SpesaTotaleEuro
FROM ClientePrivato CP JOIN Noleggio N ON CP.cliente = N.cliente
WHERE N.dataorafine IS NOT NULL
GROUP BY CP.nome, CP.cognome, CP.cliente
HAVING SUM(N.costototale) > 100.00
ORDER BY SpesaTotaleEuro DESC;


-- Query 3 - Popolarita' e costo medio dei noleggi per hub di partenza
SELECT H.citta, COUNT(N.codicenoleggio) AS NoleggiPartiti,
       AVG(N.costototale) AS CostoMedioNoleggio
FROM HubLogistico H JOIN Noleggio N ON H.codicehub = N.hubinizio
WHERE N.dataorafine IS NOT NULL
GROUP BY H.citta
ORDER BY NoleggiPartiti DESC;


-- Query 4 - Analisi operativa dei veicoli attualmente in manutenzione
SELECT V.targa, V.marca, V.modello, M.dataoraintervento, M.tipointervento,
       M.costo AS CostoIntervento, M.esito,
       T.nome AS NomeTecnico, T.cognome AS CognomeTecnico
FROM Veicolo V JOIN Manutenzione M ON V.serialeveicolo = M.veicolo
JOIN Tecnico T ON M.tecnico = T.matricola
WHERE V.statooperativo = 'In Manutenzione'
ORDER BY M.dataoraintervento DESC;


-- Query 5 - Classifica dei 5 veicoli con batterie piu' usurate
SELECT V.targa, V.marca, V.modello, B.serialebatteria,
       B.cicliricarica, B.percentualebatteria
FROM Veicolo V JOIN Batteria B ON V.serialeveicolo = B.veicolo
ORDER BY B.cicliricarica DESC
LIMIT 5;
