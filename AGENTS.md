# StockSense project context

This project is a Flask API backed by SQLAlchemy 2.x and PostgreSQL. Alembic owns
the database schema and migrations. PostgreSQL is required in every environment;
there is no SQLite fallback.

## Important integration points

- Flask application factory: `app.main:create_app`
- WSGI application: `app.main:app`
- Database engine/session: `app.database`
- SQLAlchemy models: `app.models`
- Alembic configuration: `alembic.ini` and `alembic/env.py`
- API blueprint: `app.routes.flask_api` mounted at `/api`

## Common commands

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python run.py
```

Use `docker compose up -d db` to start the local PostgreSQL service, then run
the migration command. `DATABASE_URL` is required before starting Flask or
Alembic.

When models change, create and review a migration with:

```powershell
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
```
