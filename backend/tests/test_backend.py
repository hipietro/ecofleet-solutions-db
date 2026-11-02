# File overview
# Purpose: Verify backend behavior through real HTTP requests and disposable PostgreSQL data.
# Responsibilities: Create an isolated local database and API process, prepare fixtures and
#   check critical workflows.
# Connections: Loads sql/ecofleet.sql and migrations, launches backend.app.main and removes the
#   temporary resources after the suite.

"""HTTP integration tests against a disposable local PostgreSQL database."""
# --- Imports and module dependencies ---
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import jwt
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
# Read local connection credentials; individual tests never connect to the configured DB_NAME.
load_dotenv(ROOT / '.env')


# --- Opt-in HTTP scenarios backed by an isolated local PostgreSQL database and API process. ---
@unittest.skipUnless(os.getenv('ECOFLEET_RUN_DB_TESTS') == '1', 'Set ECOFLEET_RUN_DB_TESTS=1 to run isolated database tests.')
class BackendIntegrationTests(unittest.TestCase):
    # --- Create the disposable database, apply schema scripts and wait for the isolated API server. ---
    @classmethod
    def setUpClass(cls):
        host = os.getenv('DB_HOST', 'localhost')
        # Refuse remote servers before creating any temporary resources.
        if host not in ('localhost', '127.0.0.1', '::1'):
            raise RuntimeError('Integration tests only allow a local PostgreSQL server.')
        cls.settings = dict(host=host, port=os.getenv('DB_PORT', '5432'),
                            user=os.getenv('DB_USER', 'postgres'), password=os.getenv('DB_PASSWORD', ''))
        # Generate a unique test-only name and register cleanup after database creation.
        cls.database = 'ecofleet_test_' + uuid4().hex
        cls.admin = psycopg.connect(**cls.settings, dbname='postgres', autocommit=True)
        cls.server = None
        cls.conn = None
        cls.log = tempfile.TemporaryFile(mode='w+')
        cls.admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cls.database)))
        cls.addClassCleanup(cls.cleanup)
        cls.conn = psycopg.connect(**cls.settings, dbname=cls.database, row_factory=dict_row, autocommit=True)
        # Initialize the isolated schema with the same scripts used for a new installation.
        cls.conn.execute((ROOT / 'sql/ecofleet.sql').read_text())
        for path in sorted((ROOT / 'sql/migrations').glob('*.sql')):
            cls.conn.execute(path.read_text())
        # Use a separate signing key and free port for the disposable API process.
        cls.key = secrets.token_hex(32)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.url = f'http://127.0.0.1:{port}'
        env = dict(os.environ, DB_NAME=cls.database, JWT_SECRET_KEY=cls.key)
        cls.server = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', str(port)],
            cwd=ROOT, env=env, stdout=cls.log, stderr=subprocess.STDOUT,
        )
        # Poll health with a bounded wait; include server logs if startup fails.
        for _ in range(100):
            try:
                with urlopen(cls.url + '/health', timeout=1) as response:
                    if response.status == 200:
                        return
            except OSError:
                if cls.server.poll() is not None:
                    break
                time.sleep(0.1)
        cls.log.seek(0)
        raise RuntimeError('Test server failed to start: ' + cls.log.read())

    # --- Stop the test server, close connections and drop only the generated temporary database. ---
    @classmethod
    def cleanup(cls):
        if cls.server:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait()
        if cls.conn:
            cls.conn.close()
        # The generated name is the only database this suite may drop.
        cls.admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(cls.database)))
        cls.admin.close()
        cls.log.close()

    # --- Create a distinct customer, vehicle and compatible/incompatible access points for each test. ---
    def setUp(self):
        self.cf = uuid4().hex[:16].upper()
        self.conn.execute("INSERT INTO Cliente (codicefiscale, email, dataregistrazione, saldo_crediti) VALUES (%s, %s, CURRENT_DATE, 100)",
                          (self.cf, self.cf + '@example.com'))
        self.vehicle = self.make_vehicle()
        self.hub = self.conn.execute("INSERT INTO HubLogistico (citta, indirizzo) VALUES ('Test', 'Test') RETURNING codicehub").fetchone()['codicehub']
        self.conn.execute('INSERT INTO StazioneRicarica VALUES (%s, 1, 50, 2)', (self.hub,))
        self.conn.execute("INSERT INTO PuntoAccesso VALUES (%s, 1, 1, '1'), (%s, 1, 2, '2')", (self.hub, self.hub))

    # --- Create an available electric car with its own hourly rate and trigger-generated battery. ---
    def make_vehicle(self, rate=60):
        vehicle = self.conn.execute("INSERT INTO Veicolo (marca, modello, targa, statooperativo, kmtotali) VALUES ('Test', 'Test', %s, 'Disponibile', 100) RETURNING serialeveicolo",
                                    (uuid4().hex[:20],)).fetchone()['serialeveicolo']
        self.conn.execute('INSERT INTO AutoElettrica VALUES (%s, 200, 50, %s)', (vehicle, rate))
        return vehicle

    # --- Build a test JWT, send JSON or form data and decode both successful and failed HTTP responses. ---
    def request(self, method, path, data=None, cf=None, claims=None, anonymous=False, form=False):
        # Sign short-lived fixture claims; role authorization is still read from the test database.
        payload = dict(sub=(cf or self.cf) + '@example.com', cf=cf or self.cf,
                       role='customer', exp=datetime.now(timezone.utc) + timedelta(minutes=5))
        if claims:
            payload.update(claims)
        headers = {} if anonymous else {'Authorization': 'Bearer ' + jwt.encode(payload, self.key, algorithm='HS256')}
        if data is not None:
            headers['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
        encoded = (urlencode(data) if form else json.dumps(data)).encode() if data is not None else None
        request = Request(self.url + path, data=encoded, headers=headers, method=method)
        # Decode successful and error HTTP responses through the same helper.
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    # --- Send a rental-start request using the current fixture or explicit customer and vehicle overrides. ---
    def start(self, cf=None, vehicle=None, point=1):
        return self.request('POST', '/api/rentals/start', dict(veicolo=vehicle or self.vehicle,
                            hubinizio=self.hub, stazioneinizio=1, puntoinizio=point), cf=cf)

    # --- Send a rental-stop request using the fixture return point and mileage. ---
    def stop(self, rental, point=1):
        return self.request('POST', '/api/rentals/stop', dict(codicenoleggio=rental,
                            hubfine=self.hub, stazionefine=1, puntofine=point, km_percorsi=7))

    # --- Start a rental and move its start time back to exercise two-minute billing deterministically. ---
    def active_rental(self):
        code, body = self.start()
        self.assertEqual(code, 200, body)
        rental = body['codicenoleggio']
        self.conn.execute("UPDATE Noleggio SET dataorainizio = date_trunc('second', clock_timestamp()) - INTERVAL '61 seconds' WHERE codicenoleggio=%s", (rental,))
        return rental

    # --- Verify vehicle-specific prices, combined filters, detail output and a missing vehicle. ---
    def test_fleet_rates_filters_and_detail(self):
        other = self.make_vehicle(120)
        code, rows = self.request('GET', '/api/fleet/vehicles?stato=Disponibile&marca=Test')
        self.assertEqual(code, 200, rows)
        rates = {row['serialeveicolo']: Decimal(row['costoorario']) for row in rows}
        self.assertEqual(rates[self.vehicle], 60)
        self.assertEqual(rates[other], 120)
        code, row = self.request('GET', f'/api/fleet/vehicles/{other}')
        self.assertEqual((code, Decimal(row['costoorario'])), (200, 120))
        self.assertEqual(self.request('GET', '/api/fleet/vehicles/-1')[0], 404)

    # --- Verify the charge, wallet balance, single mileage update, receipt and repeat-stop rejection. ---
    def test_stop_uses_one_price_and_updates_mileage_once(self):
        rental = self.active_rental()
        code, body = self.stop(rental)
        self.assertEqual(code, 200, body)
        self.assertEqual(Decimal(body['costo_totale']), Decimal('3.00'))
        self.assertEqual(Decimal(body['saldo_rimanente']), Decimal('97.00'))
        self.assertEqual(self.conn.execute('SELECT kmtotali FROM Veicolo WHERE serialeveicolo=%s', (self.vehicle,)).fetchone()['kmtotali'], 107)
        self.assertEqual(self.conn.execute('SELECT count(*) AS n FROM Ricevuta WHERE noleggio=%s', (rental,)).fetchone()['n'], 1)
        self.assertEqual(self.stop(rental)[0], 404)
        self.assertEqual(self.conn.execute('SELECT costototale FROM Noleggio WHERE codicenoleggio=%s', (rental,)).fetchone()['costototale'], Decimal(body['costo_totale']))

    # --- Verify that the Premium discount combines with a vehicle-specific rate and unlock fee. ---
    def test_corporate_discount_and_per_vehicle_rate(self):
        self.conn.execute("UPDATE Cliente SET ruolo='corporate' WHERE codicefiscale=%s", (self.cf,))
        self.conn.execute("INSERT INTO ClienteCorporate VALUES (%s, 'Test Company', %s, 'Premium')", (self.cf, uuid4().hex[:20]))
        self.conn.execute('UPDATE AutoElettrica SET costoorario=120 WHERE veicolo=%s', (self.vehicle,))
        code, body = self.stop(self.active_rental())
        self.assertEqual(code, 200, body)
        self.assertEqual(Decimal(body['costo_totale']), Decimal('4.25'))

    # --- Verify that invalid returns and insufficient credit leave the rental, vehicle and receipts unchanged. ---
    def test_failed_stop_rolls_back_all_changes(self):
        rental = self.active_rental()
        self.assertEqual(self.stop(rental, point=2)[0], 400)
        self.conn.execute('UPDATE Cliente SET saldo_crediti=0 WHERE codicefiscale=%s', (self.cf,))
        self.assertEqual(self.stop(rental)[0], 400)
        self.assertIsNone(self.conn.execute('SELECT dataorafine FROM Noleggio WHERE codicenoleggio=%s', (rental,)).fetchone()['dataorafine'])
        row = self.conn.execute('SELECT kmtotali, statooperativo FROM Veicolo WHERE serialeveicolo=%s', (self.vehicle,)).fetchone()
        self.assertEqual(row, dict(kmtotali=100, statooperativo='In Uso'))
        self.assertEqual(self.conn.execute('SELECT count(*) AS n FROM Ricevuta WHERE noleggio=%s', (rental,)).fetchone()['n'], 0)

    # --- Verify connector and battery validation without leaving the vehicle unavailable. ---
    def test_start_checks_battery_and_rolls_back_invalid_point(self):
        self.assertEqual(self.start(point=2)[0], 400)
        self.conn.execute('UPDATE Batteria SET percentualebatteria=14 WHERE veicolo=%s', (self.vehicle,))
        self.assertEqual(self.start()[0], 400)
        self.assertEqual(self.conn.execute('SELECT statooperativo FROM Veicolo WHERE serialeveicolo=%s', (self.vehicle,)).fetchone()['statooperativo'], 'Disponibile')

    # --- Verify that competing starts for one account create only one active rental. ---
    def test_simultaneous_starts_allow_one_rental(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.start(), range(2)))
        self.assertEqual(sorted(status for status, _ in results), [200, 400])

    # --- Verify that different customers cannot concurrently acquire the same vehicle. ---
    def test_two_customers_cannot_rent_the_same_vehicle(self):
        other = uuid4().hex[:16].upper()
        self.conn.execute('INSERT INTO Cliente (codicefiscale, email, dataregistrazione) VALUES (%s,%s,CURRENT_DATE)', (other, other+'@example.com'))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda cf: self.start(cf=cf), [self.cf, other]))
        self.assertEqual(sorted(status for status, _ in results), [200, 400])

    # --- Verify that simultaneous completion requests debit the wallet exactly once. ---
    def test_simultaneous_stops_charge_once(self):
        rental = self.active_rental()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.stop(rental), range(2)))
        self.assertEqual(sorted(status for status, _ in results), [200, 404])
        self.assertEqual(self.conn.execute('SELECT saldo_crediti FROM Cliente WHERE codicefiscale=%s', (self.cf,)).fetchone()['saldo_crediti'], Decimal('97.00'))

    # --- Verify nested history details, unknown-account rejection and isolation between customers. ---
    def test_history_belongs_to_current_customer(self):
        self.active_rental()
        code, rows = self.request('GET', '/api/rentals/me')
        self.assertEqual(code, 200, rows)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['veicolo_dettagli']['serialeveicolo'], self.vehicle)
        self.assertEqual(self.request('GET', '/api/rentals/me', cf='NONEXISTENT00001')[0], 401)
        other = uuid4().hex[:16].upper()
        self.conn.execute('INSERT INTO Cliente (codicefiscale, email, dataregistrazione) VALUES (%s,%s,CURRENT_DATE)', (other, other+'@example.com'))
        self.assertEqual(self.request('GET', '/api/rentals/me', cf=other), (200, []))

    # --- Verify phone persistence, login and atomic rejection of duplicate account or license data. ---
    def test_registration_preserves_phone_and_handles_duplicates(self):
        data = dict(codicefiscale=uuid4().hex[:16].upper(), email=uuid4().hex+'@example.com',
                    telefono='0123456789', password='test-password', nome='Test', cognome='Example', numero_patente=uuid4().hex[:15])
        code, body = self.request('POST', '/api/auth/register', data, anonymous=True)
        self.assertEqual(code, 201, body)
        row = self.conn.execute('SELECT telefono FROM Cliente WHERE codicefiscale=%s', (data['codicefiscale'],)).fetchone()
        self.assertEqual(row['telefono'], data['telefono'])
        self.assertEqual(self.request('POST', '/api/auth/register', data, anonymous=True)[0], 400)
        code, login = self.request('POST', '/api/auth/login', dict(username=data['email'], password=data['password']), anonymous=True, form=True)
        self.assertEqual(code, 200, login)
        self.assertIn('access_token', login)
        self.assertEqual(self.request('POST', '/api/auth/login', dict(username=data['email'], password='wrong'), anonymous=True, form=True)[0], 401)
        data.update(codicefiscale=uuid4().hex[:16].upper(), email=uuid4().hex+'@example.com')
        self.assertEqual(self.request('POST', '/api/auth/register', data, anonymous=True)[0], 400)
        self.assertIsNone(self.conn.execute('SELECT codicefiscale FROM Cliente WHERE codicefiscale=%s', (data['codicefiscale'],)).fetchone())

    # --- Verify that oversized multi-byte passwords fail validation before hashing. ---
    def test_registration_rejects_oversized_utf8_password(self):
        data = dict(codicefiscale=uuid4().hex[:16].upper(), email=uuid4().hex+'@example.com',
                    password='é'*40, nome='Test', cognome='Test', numero_patente='TEST12345')
        self.assertEqual(self.request('POST', '/api/auth/register', data, anonymous=True)[0], 422)

    # --- Verify company registration fields and rejection of unsupported contract levels. ---
    def test_corporate_registration_sets_date_and_role(self):
        data = dict(codicefiscale=uuid4().hex[:16].upper(), email=uuid4().hex+'@example.com',
                    telefono='0123456789', password='test-password', ragionesociale='Test Company',
                    partitaiva=uuid4().hex[:20], livellocontratto='Premium')
        code, body = self.request('POST', '/api/auth/register/corporate', data, anonymous=True)
        self.assertEqual(code, 201, body)
        row = self.conn.execute('SELECT ruolo, dataregistrazione FROM Cliente WHERE codicefiscale=%s', (data['codicefiscale'],)).fetchone()
        self.assertEqual(row['ruolo'], 'corporate')
        self.assertIsNotNone(row['dataregistrazione'])
        data.update(codicefiscale=uuid4().hex[:16].upper(), email=uuid4().hex+'@example.com', livellocontratto='unknown')
        self.assertEqual(self.request('POST', '/api/auth/register/corporate', data, anonymous=True)[0], 422)

    # --- Verify staff authorization, database role refresh and maintenance-state validation. ---
    def test_technician_can_log_maintenance(self):
        technician = uuid4().hex[:20]
        data = dict(veicolo=self.vehicle, tecnico=technician, dataoraintervento='2026-01-01',
                    tipointervento='Test', costo='10.00', esito='Test', nuovo_stato_veicolo='In Manutenzione')
        self.assertEqual(self.request('POST', '/api/backoffice/maintenance', data)[0], 403)
        self.conn.execute("UPDATE Cliente SET ruolo='technician' WHERE codicefiscale=%s", (self.cf,))
        self.conn.execute("INSERT INTO Tecnico VALUES (%s, 'Test', 'Test', 'Test')", (technician,))
        code, body = self.request('POST', '/api/backoffice/maintenance', data)
        self.assertEqual(code, 201, body)
        data['nuovo_stato_veicolo'] = 'invalid'
        self.assertEqual(self.request('POST', '/api/backoffice/maintenance', data)[0], 422)

    # --- Verify missing/expired tokens, database-backed roles and real payment-method presence. ---
    def test_authentication_and_authorization(self):
        self.assertEqual(self.request('GET', '/api/auth/me', anonymous=True)[0], 401)
        self.assertEqual(self.request('GET', '/api/auth/me', claims=dict(exp=datetime.now(timezone.utc)-timedelta(seconds=1)))[0], 401)
        self.assertEqual(self.request('GET', '/api/backoffice/analytics/kpi', claims=dict(role='manager'))[0], 403)
        self.conn.execute("UPDATE Cliente SET default_payment_method='test-method' WHERE codicefiscale=%s", (self.cf,))
        code, profile = self.request('GET', '/api/auth/me')
        self.assertEqual((code, profile['has_payment_method']), (200, True))

    # --- Verify that the stabilization migration is repeatable without breaking existing account access. ---
    def test_migration_can_be_reapplied(self):
        self.conn.execute((ROOT / 'sql/migrations/001_api_stabilization.sql').read_text())
        self.assertEqual(self.request('GET', '/api/auth/me')[0], 200)


if __name__ == '__main__':
    unittest.main()
