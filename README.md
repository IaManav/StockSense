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

The demo account includes a main warehouse, receiving/rack/production
locations, three products, stock quantities, a completed receipt, a ready
delivery, a ready internal transfer, a draft adjustment, and ledger entries.

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

For local password recovery, click `Forgot password?` on the Login card, enter
the account email, and request a code. In Flask debug mode the development OTP
is shown in the reset dialog. In production, connect that endpoint to your
email provider instead of exposing the OTP.

## Account validation

Signup and password changes require a valid email address and a password with
at least 8 characters, one uppercase letter, one number, and one special
character. These rules are enforced by the API as well as the browser form.
