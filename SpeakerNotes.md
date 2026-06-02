Paylink — Speaker Notes (Detailed)

Purpose: These notes explain the system in detail and point to exact files and code locations to reference during the presentation.

1) Entry point & server
- File: [app.py](app.py)
- What to show: routes defined for UI pages (e.g., `@app.route('/transfer')`), API endpoints (e.g., `/api/oracle/rates`, `/api/admin/*`).
- Where to edit: top-level route handlers and API route functions inside `app.py`.

2) Database abstraction
- File: [oop_banking.py](oop_banking.py)
- Key classes: `DatabaseManager` base, `OracleDatabaseManager`, `SQLiteDatabaseManager` (search for "class OracleDatabaseManager" in file).
- Where provider is selected: `get_db_manager()` at the bottom of `oop_banking.py`.
- Important methods: `get_connection()`, `register_customer()`, `add_transaction()`, `get_transactions()` in the Oracle manager implementation.

3) App-level helpers
- File: [database.py](database.py)
- Purpose: adapts domain objects to legacy view dicts, exposes functions used by `app.py` routes (e.g., `register_user()`, `get_user_by_id()`, `add_transaction()`).
- Note: balance persistence is done via `oop_banking` managers — see `_persist_balance()` and `update_balance()`.

4) Oracle integration & rates
- File: [oracle.py](oracle.py)
- Function: `fetch_oracle_rates()` (caching + external fetch). API endpoint in `app.py` is `/api/oracle/rates` which returns this payload.
- To change provider: set `ORACLE_ENDPOINT` environment variable.

5) Schema & provisioning
- Files: [oracle_schema.sql](oracle_schema.sql), [setup_oracle.py](setup_oracle.py)
- Run `oracle_schema.sql` in SQL Developer or run `python setup_oracle.py` to create the schema objects.

6) Frontend templates
- Directory: `templates/`
- Transfer UI: [templates/transfer.html](templates/transfer.html#L1)
  - Destination bank list and the exchange-rate box are in this file.
  - The client-side flow for transfers and PIN modal lives in the `<script>` section near the bottom.
- Admin UI: [templates/admin.html](templates/admin.html)
  - Tabs and fetches to `/api/admin/*` endpoints are implemented here.

7) Static assets
- `static/main.js`: client-side helpers and functions — `fetchOracleRates()` and transfer flow helpers are declared here.
- `static/style.css`: UI styles including bottom nav.

8) Running locally
- Ensure env vars are set: `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PWD`, `DATABASE_PROVIDER=oracle`.
- Start app: `python app.py` and open `http://127.0.0.1:5000`.

9) Admin credentials / seeded users
- During schema init, admin staff may be seeded. Check `oop_banking.py` in the `init_db()` implementation inside the `OracleDatabaseManager` section where a default admin hash is inserted if no bank_staff exists.

10) Git & repo
- README added at repository root: [README.md](README.md)
- To commit and push your local changes:

```bash
git add README.md Presentation.md SpeakerNotes.md
git commit -m "Docs: README + presentation + speaker notes"
git push origin HEAD
```

11) Troubleshooting
- If `RuntimeError` about Oracle occurs when `get_db_manager()` runs: confirm env vars and that the service in `ORACLE_DSN` is reachable (try pinging host or connecting via SQL Developer).
- Use Oracle SQL Developer to inspect tables after provisioning: connect with the same `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PWD`.

Notes for the live demo:
- Show dashboard after logging in to demonstrate seeded data.
- Visit `Transfer` to highlight the live Oracle rate and destination bank list.
- Open `Admin` to show users, transactions, and audit logs.

If you want, I can:
- Commit and push these documentation files for you.
- Generate a PowerPoint `.pptx` from `Presentation.md` and attach it.
- Expand any slide into more speaker notes or code excerpts.
