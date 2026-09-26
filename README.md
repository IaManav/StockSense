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

The API is available at `http://localhost:5000`; health checks are at `/health`.
`DATABASE_URL` must be a PostgreSQL SQLAlchemy URL. See `AGENTS.md` for the
project conventions and integration points.
