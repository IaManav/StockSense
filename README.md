# StockSense

StockSense is a Flask inventory API using SQLAlchemy 2.x, PostgreSQL, and
Alembic migrations.

## Local setup

1. Install Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Start PostgreSQL:

   ```powershell
   docker compose up -d db
   ```

3. Configure the application:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Apply migrations and start Flask:

   ```powershell
   alembic upgrade head
   python run.py
   ```

The web interface is available at `http://localhost:5000`; health checks are at
`/health`, and the JSON API is mounted under `/api`. The interface is a
server-rendered Flask shell with a lightweight vanilla JavaScript client, so no
separate frontend build step or Node installation is required.

`DATABASE_URL` must be a PostgreSQL SQLAlchemy URL. See `AGENTS.md` for the
project conventions and integration points.

## Load demo data

After PostgreSQL is running and migrations are applied, load the repeatable
demo dataset:

```powershell
python -m scripts.seed_demo
```

The seeder is safe to run more than once; it checks the demo references and
unique fields before inserting records. Use these credentials in the web app:

```text
Login ID: demo01
Password: Demo123!
```

Warehouse staff demo:

```text
Login ID: staff01
Password: Staff123!
```

The demo data includes two warehouses, receiving/storage/production/dispatch
locations, varied products and stock levels, reserved and out-of-stock items,
draft/ready/waiting/done receipts and deliveries, transfers, adjustments, and
ledger movements so each major workflow is visible in the UI.

## Using the app

1. Open `http://localhost:5000`.
2. Sign in with the demo credentials, or create your own account.
3. Use Dashboard for stock KPIs and quick actions.
4. Use Products to search the catalogue and Stock by location to inspect free
   quantities.
5. Use Receipts for incoming goods, Deliveries for outgoing goods, Internal
   transfers for warehouse movements, and Adjustments for physical counts.
6. Use Move history to audit validated stock movements.
7. Use Warehouses to configure warehouses and their locations.

Operations follow the intended workflow: create a document, add its product
lines, mark it Ready, then validate it. Validation is the point at which stock
and the ledger are updated.

Receipt and delivery references are generated automatically in the format
`<WAREHOUSE>/IN/001` or `<WAREHOUSE>/OUT/001`. The number is incremented for
that warehouse and operation type. Receipt destinations use the warehouse and
location format, such as `WH/STOCK1`.

For password recovery, click `Forgot password?` on the Login card, enter the
account email, and request a code. StockSense sends the one-time code through
the configured SMTP server. Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
`SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_USE_TLS` in `.env` before using this
flow. Codes are stored only as hashes and expire after 10 minutes.

## Account validation

Signup and password changes require a valid email address and a password with
at least 8 characters, one uppercase letter, one number, and one special
character. These rules are enforced by the API as well as the browser form.
