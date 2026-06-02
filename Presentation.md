# Paylink Presentation — Veritas Microfinance Bank

---

# Slide 1 — Title
Paylink — Veritas Microfinance Bank
- A secure student & faculty digital banking platform built with Flask + Oracle

Speaker: (Your name)

---

# Slide 2 — Agenda
- Project overview
- Architecture & components
- Demo walkthrough (login, dashboard, transfer, admin)
- Oracle integration & live exchange rates
- Code map (where to locate features)
- Deployment & next steps

---

# Slide 3 — System Overview
- Flask application server (`app.py`) serving Jinja templates and REST APIs
- Oracle Database for persistence via `oop_banking.py` managers
- Frontend: responsive templates in `templates/` with `static/` JS & CSS

---

# Slide 4 — Architecture Diagram
- Web client (browser) ↔ Flask (`app.py`) ↔ Oracle (`oop_banking.py`)
- Helper modules: `database.py` (app bridge), `oracle.py` (external rates)

---

# Slide 5 — Key Features
- Customer registration & login
- Wallet balances, transfers (NIP-like flow)
- Virtual cards, bill payments, notifications
- Admin Control Panel (users, ledger, fraud, audit logs)
- Oracle-backed persistence and audit triggers
- Live exchange rates fetched from `oracle.fetch_oracle_rates()`

---

# Slide 6 — Demo Steps
1. Start Oracle and ensure schema via `oracle_schema.sql` or `setup_oracle.py`.
2. Set env vars (`ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PWD`, `DATABASE_PROVIDER=oracle`).
3. Run `python app.py` and open `http://127.0.0.1:5000`.
4. Login with seeded admin user (if seeded) or register a new user.
5. Visit `Transfer` to demonstrate live Oracle rate and transfer flow.
6. Open `Admin` to inspect users, transactions, and audit logs.

---

# Slide 7 — Code Map (Quick)
- `app.py`: routes & APIs
- `oop_banking.py`: database manager implementations (Oracle/SQLite)
- `database.py`: higher-level functions used by routes
- `oracle.py`: external rate fetcher
- `templates/`: per-page HTML (e.g., `transfer.html`, `admin.html`)
- `static/`: `main.js`, `style.css`

---

# Slide 8 — Security & Auditing
- Passwords stored as SHA-256 hashes in the DB
- Database triggers keep audit logs on sensitive updates
- Admin audit logs available at `/api/admin/audit-logs`

---

# Slide 9 — Deployment & Ops Notes
- Use environment variables for secrets
- CI: push to GitHub, deploy to your cloud host with Oracle network routing
- For development, Oracle XE or a Dockerized Oracle instance is recommended

---

# Slide 10 — Q&A / Next Steps
- Demo user flows
- Discuss additional features (KYC, rate-provider redundancy)

---

# Appendix — Helpful Commands
```bash
python setup_oracle.py    # create schema objects
python app.py            # run the web app
git push origin HEAD     # push changes
```