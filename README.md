# Paylink — Veritas Microfinance Bank (Developer README)

This repository contains Paylink, a Flask-based digital banking frontend and backend wired to Oracle Database.

## Quick Overview
- App: `app.py` (Flask)
- Main DB abstraction: `oop_banking.py` (polymorphic managers)
- App-to-DB bridge: `database.py`
- Oracle rate helper: `oracle.py`
- Oracle DDL: `oracle_schema.sql` and `setup_oracle.py`
- Frontend: `templates/` and `static/`

## Requirements
Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Ensure `oracledb` is installed (already in `requirements.txt`).

## Environment Variables
Set these before running the app (Windows example):

```powershell
setx ORACLE_DSN "localhost:1521/XE"
setx ORACLE_USER "VERITAS_ADMIN"
setx ORACLE_PWD "YourSecurePassword"
```

On macOS / Linux use `export` instead of `setx`.

- `ORACLE_DSN`: host:port/SERVICE_NAME (e.g. `localhost:1521/XE`)
- `ORACLE_USER`: Oracle user (e.g. `VERITAS_ADMIN`)
- `ORACLE_PWD`: Oracle password

## Provision Oracle Schema
Option A — Use `sqlcl` / SQL Developer / sqlplus
1. Open Oracle SQL Developer and connect using the same values above.
2. Run the file `oracle_schema.sql` (located at repository root). This creates sequences, tables, triggers and required stored procedures.

Option B — Use the bundled `setup_oracle.py` (convenience script — requires the executing user to have privileges to create objects):

```bash
python setup_oracle.py
```

The script will connect using values inside oracledb defaults (edit the script or use environment variables before running).

## Running the App (Local)
1. Ensure environment variables are set and Oracle is reachable.
2. Start Flask:

```bash
python app.py
```

3. Visit `http://127.0.0.1:5000`.

## Admin Panel
- Web admin UI: `http://127.0.0.1:5000/admin` (served by `app.py` route `admin()`)
- Admin APIs live under `/api/admin/*` in `app.py` (e.g., `/api/admin/users`, `/api/admin/transactions`).
- Admin UI is implemented in `templates/admin.html` and uses client-side fetches to those API endpoints.

## Oracle Live Rates
- The app fetches exchange rates through the `/api/oracle/rates` endpoint (in `app.py`) which calls `oracle.fetch_oracle_rates()`.
- Configure `ORACLE_ENDPOINT` env var to point to your preferred rate provider (default used: `https://open.er-api.com/v6/latest/USD`).

## Code Map (where to find things)
- Views / Routes: `app.py`
- Database models / managers: `oop_banking.py`
- App-level helpers and logical operations: `database.py`
- Oracle helper / rate fetcher: `oracle.py`
- Database schema: `oracle_schema.sql`, `setup_oracle.py`
- Frontend templates: `templates/` (per-page HTML)
- Static assets: `static/` (`main.js`, `style.css`)

## Pushing changes
We use `origin` remote. Example:

```bash
git add .
git commit -m "Your message"
git push origin HEAD
```

## Troubleshooting
- If `get_db_manager()` raises a RuntimeError, verify `ORACLE_*` env vars and that `oracledb` is installed.
- If schema objects are missing, run `oracle_schema.sql` from SQL Developer.

---

If you want, I can add these README changes to the repo and push them now.