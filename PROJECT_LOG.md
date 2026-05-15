# Project Log — Personal Finance Tool

## 2026-05-15 (end of session)
- Built `confirm.html` — column mapping preview template
  - Preview table renders headers as dropdowns + sample rows as data
  - Dropdown options: Ignore / Date / Description / Amount / Debit / Credit
  - Auto-guess uses case-insensitive `header.lower()` checks (e.g. `'date' in header.lower()`)
  - Description auto-guess catches both `'desc'` and `'memo'` column naming conventions
  - `<form>` wraps entire table so all dropdowns are submitted together
  - Confirm and Go Back buttons placed below the table
  - `loop.index0` used for dropdown names (`mapping_0`, `mapping_1`, etc.) — matches `upload_confirm` logic
- Resolved open question from CLAUDE.md: file held between steps via Flask session (`session['uploaded_file']`)
- Fixed `UndefinedError: 'int object' has no attribute 'lower'` — caused by `pd.read_csv(header=None)` returning integer column indices; fixed by converting all columns to strings
- Tested against a real Chase CSV (no header row, 7 columns); identified column layout: transaction date, post date, description, Chase category, transaction type, amount, empty trailing column
- Decisions for next session — column mapping dropdown options need expanding:
  - Split `Date` into `Transaction Date` and `Post Date` (two separate options); if only one date column present, default to Transaction Date
  - Add `Category` option mapping to `api_category` field (for bank-provided categories like Chase exports)
  - Auto-guess for `Category`: `'categ' in header.lower()`
  - Full target dropdown set: Ignore / Transaction Date / Post Date / Description / Amount / Debit / Credit / Category
- Next: update `confirm.html` with expanded dropdown options, then implement `upload_confirm()` route logic

## 2026-05-14 (end of session)
- Built out Step 2 (column mapping) scaffolding in `routes/upload.py`
- Added `has_headers` checkbox to `upload.html` — checked by default; if unchecked, `pd.read_csv()` uses `header=None` to avoid treating first data row as headers
- After file save, reads first 5 rows with Pandas and passes `headers` and `sample_rows` to `confirm.html` template (not yet built)
- Stores file path in `session['uploaded_file']` to persist between Step 1 and Step 2
- Added `upload_confirm()` route stub at `POST /upload/confirm` using `upload_bp` decorator
- Designed `upload_confirm` logic: retrieve file path from session, collect per-column mapping from form (keys like `mapping_0`, `mapping_1`), validate that Date/Description/Amount are assigned, store confirmed mapping in `session['column_mapping']` for Step 3
- Next: build `confirm.html` preview table with per-column dropdowns (Date / Description / Amount / Debit / Credit / Ignore), then implement `upload_confirm` logic

## 2026-05-13 (end of session)
- Started implementing Step 1 (file validation) in `routes/upload.py`
- Added `ALLOWED_EXTENSIONS = {'csv', 'ofx'}` and `allowed_file()` helper at top of file
- Fixed validation check ordering: no-file-in-request → empty filename → `allowed_file()` → save; earlier draft had checks after `file.save()` which would have crashed
- Added `else` branch to flash a clear error and redirect if file type is not allowed
- Added `os.makedirs('uploads', exist_ok=True)` to `app.py` so uploads folder is created at startup
- Decided to keep uploaded files on disk (not discard after processing) — useful for debugging bad imports and re-processing
- Note: `qfx` still missing from `ALLOWED_EXTENSIONS` — to fix next session
- Note: `uploads/` path is currently relative; revisit absolute path and per-household subfolders post-v1
- Next: add `qfx` to allowed extensions, then move on to Step 2 (column mapping)

## 2026-05-10 (end of session)
- Removed duplicate `/upload` route from `app.py` — Blueprint in `routes/upload.py` is now the sole handler; completes the Blueprint refactor to-do
- Designed the upload validation pipeline — 3-step gate before any data is written:
  - Step 1: file-level checks (type, size, non-empty, OFX header) — hard reject
  - Step 2: column mapping UI — preview table with auto-guessed header dropdowns; user confirms before proceeding
  - Step 3: column validation — hard reject on any bad row, with specific error message (row number, column, value)
- Decided to start with strict/unforgiving validation rules and relax only if real usage demands it
- Noted debit/credit two-column pattern (common in bank CSV exports) as a known edge case — normalizer will need to combine them into a single signed amount
- Open question: how to hold the uploaded file between Step 2 and Step 3 — staging table, temp file, or server-side session; not resolved yet

## 2026-05-09 (end of session)
- Added `transactions/` to `.gitignore` — folder contains real bank data, must not be committed
- Set up Flask Blueprint structure for upload route: created `routes/` package with `__init__.py` and `upload.py`
- Moved `REGISTRY_PATH` from `app.py` into `database/db.py` so it can be imported by both `app.py` and `routes/upload.py`
- Registered Blueprint in `app.py` with `app.register_blueprint(upload_bp)`
- Built `upload.html` form with file input, `enctype="multipart/form-data"`, and `name="file"` attribute
- Old stub `/upload` route in `app.py` still needs to be removed — deferred to next session
- Next: remove stub route, then build real upload logic in `routes/upload.py`

## 2026-05-07 (end of session — continued)
- Added `/logout` route: clears session, flashes success message, redirects to `/`
- Added stub routes for `/transactions`, `/accounts`, `/upload`, `/adduser` — each renders a "Coming soon" template
- Created stub templates: `transactions.html`, `accounts.html`, `upload.html`, `add_user.html`
- All navigation links working; no 404s on logged-in nav
- Next: build out `/upload` route with real CSV/OFX file upload and parsing logic

## 2026-05-07 (end of session)
- Built index route: replaced `'Finance Tool is running.'` placeholder with `render_template('index.html')`
- Built `index.html` template with conditional content: logged-in users see navigation links (Transactions, Accounts, Upload, Add Member); logged-out users see Log In and Create Household links
- Index route confirmed working — flash messages (e.g. "Login successful") now display correctly after login
- Next: build `/logout` route, then stub out remaining routes (`/transactions`, `/accounts`, `/upload`, `/adduser`)

## 2026-05-06 (end of session)
- Fixed `household_new.html` — email field was missing `required` attribute and label said "optional"; corrected both
- Built `/login` route (GET + POST):
  - GET fetches all households from `registry.db` and passes them to template as a dropdown
  - POST validates fields, looks up household in `registry.db` to get `database_path`, queries household DB for user, checks password with `verify_password()`, stores `user_id` and `household_db_path` in session
- Built `login.html` template with household dropdown, username, and password fields
- Fixed `login.html` block name: `{% block content %}` → `{% block main %}` to match `layout.html`
- Fixed flash message display in `layout.html`: replaced double `get_flashed_messages()` call (which consumed messages before rendering) with `{% set messages %}` pattern; added `with_categories=true` so Bootstrap alert color matches flash category
- Login route confirmed working — redirects to `/` on success
- Flash message not visible yet because `/` returns a plain string, not a template; will resolve when index route is built
- Next: build index route and template

## 2026-05-04 (end of session)
- Added email field to `household_new.html` and `app.py` (form collection, validation, INSERT)
- Added basic email format check (`@` and `.` present)
- Added `os.makedirs('data', exist_ok=True)` before `init_registry()` in `app.py` so `data/` is created on fresh start
- `/household/new` fully working — tested successfully; household and admin user verified in SQLite
- Next: build `/login` route and template

## 2026-05-04 (end of session — mid-test)
- Fixed `registry_schema.sql` — added `IF NOT EXISTS` to `CREATE TABLE households` to prevent error on repeated startup
- Added `os.makedirs('data', exist_ok=True)` to `app.py` before `init_registry()` call
- First test of `/household/new` hit `sqlite3.IntegrityError: NOT NULL constraint failed: users.email` — `email` column is NOT NULL but form and INSERT didn't include it
- Decided to add email to the form rather than make the column nullable
- Next: add email field to `household_new.html`, add `email` to form field collection and INSERT in `app.py`, delete `data/` folder to clear partially-created household, then retest

## 2026-05-04 (end of session)
- Added imports to `app.py`: `uuid`, `get_db`, `init_db`, `hash_password`, updated Flask imports
- Wrote `/household/new` route (GET + POST):
  - POST validates: creation code, all fields present, password >= 8 chars, passwords match, household name uniqueness
  - Creation block: generates `uuid` for file naming, creates `data/{id}/` directory, calls `init_db()`, inserts admin user into household DB, registers household in `registry.db`
  - GET renders `household_new.html` template (not yet written)
- Next: write `household_new.html` template, then `/login` and `/` routes

## 2026-05-03 (end of session)
- Added `init_registry()` to `database/db.py` — targets `registry_schema.sql` and `registry.db`
- Decided UI flow: unauthenticated home screen shows login form + "Add Household" button (top right)
- Decided household creation gate: `/household/new` form requires a `CREATION_CODE` env var (stored in `.env`, excluded from git); plain secret is sufficient for this threat model — hardening deferred to pre-submission to-do
- Cleaned up `templates/layout.html`: added `<!DOCTYPE html>`, replaced CS50 navbar brand with "Household Finance", replaced stock-trading nav links with app routes (Transactions, Accounts, Upload, AddUser), removed Register link from logged-out nav, removed W3C validator footer, removed global `text-center` from `<main>`
- Added `python-dotenv==1.2.2` to `requirements.txt`
- Updated `app.py`: added `load_dotenv()`, `app.secret_key` from env, `REGISTRY_PATH`, and `init_registry()` call at startup
- Created `.env` with `SECRET_KEY` and `CREATION_CODE` (excluded from git)
- Next: write `/household/new` route (GET + POST) and `household_new.html` template, then `/login` and `/` routes

## 2026-04-22 (end of session)
- Added `init_db(db_path)` function to `database/db.py`
  - Uses `os.path.dirname(__file__)` to build a reliable path to `schema.sql` regardless of working directory
  - Calls `get_db()` to open the connection, then `executescript()` to run the full schema in one call
  - Closes the connection after — `init_db` is setup only, does not return a connection
- Added `import os` to top of `db.py`
- Decided household database files live in `data/{id}/{id}.db` — one subfolder per household for OS-level permission isolation
- Decided `registry.db` lives in `data/` — tracks household names and their database paths; separate from household DBs
- Created `database/registry_schema.sql` with a single `households` table: `id`, `name` (UNIQUE), `database_path`, `created_at`
- Added comment above `CREATE INDEX idx_transactions_dedup_hash` in `schema.sql` explaining why the index exists
- Next: write `init_registry()` in `db.py` and the household registration route in `app.py`

## 2026-04-17 (end of session)
- Wrote `accounts` table in schema.sql
- Removed Copilot-suggested `user_id` FK — accounts are household-level; user↔account relationships belong in `account_members` junction table
- Fixed trailing comma syntax error left by Copilot
- Wrote `account_members` junction table: composite PK on (user_id, account_id), role CHECK ('owner'/'member'), CASCADE deletes on both FKs
- Decided against `viewer` role in `account_members` — read-only access is already handled by `rights` in `users` table
- Wrote `statements` table: account_id FK, filename, filetype CHECK ('csv'/'ofx'), date_start, date_end, imported_at, optional description
- Wrote `transactions` table: all fields per CLAUDE.md design; added `statement_id` nullable FK to trace transactions back to source upload; decided to use BOOLEAN for pending (stored as INTEGER by SQLite)
- Added SQL comments at top of schema.sql describing each table
- Wrote `categories` table: id, name (UNIQUE), nullable self-referencing parent_id FK with SET NULL on delete
- Wrote `categorization_rules` table: description_pattern, merchant_pattern, source_pattern (all nullable but CHECK ensures at least one is set), category_id FK with RESTRICT on delete, priority INTEGER
- Decided RESTRICT on category delete for rules — prevents orphaned rules, can revisit if burdensome
- Schema is complete — all 7 tables written
- Created .gitignore (excludes venv/, *.db, __pycache__, .env, .DS_Store)
- Setting up GitHub: created `projects` master index repo and `finance-tool` repo on GitHub (both public)
- Created README.md in ~/projects/ linking to finance-tool repo
- Installed GitHub CLI (`gh`), authenticated via browser
- Pushed both `projects` and `finance-tool` repos to GitHub
- Created CLAUDE_CONTEXT.md in projects repo — persistent context file for Claude.ai sessions

## 2026-04-19
- Security review prompted by Claude.ai — four areas identified: password hashing, path traversal, SQL injection, dedup hash column
- Added `dedup_hash TEXT NOT NULL UNIQUE` to transactions table — was missing despite being specified in CLAUDE.md
- Added `CREATE INDEX idx_transactions_dedup_hash` for fast deduplication lookups during import
- Schema is now fully complete and security-reviewed
- Next: implement password hashing and auth foundation

## 2026-04-19 (continued)
- Created `core/auth.py` with `hash_password` and `verify_password` functions using Werkzeug
- Decided to use Werkzeug (pbkdf2:sha256) over bcrypt — already a Flask dependency, sufficient for this threat model
- Tested auth functions with a small test script; confirmed correct and deleted test script
- Created `database/db.py` with `get_db(db_path)` function — opens SQLite connection, sets row_factory, enables FK enforcement via PRAGMA
- Next: database initialization code (creates tables from schema.sql on first run)

## 2026-04-14 (end of session)
- Discussed auth approach: will use Werkzeug (`generate_password_hash` / `check_password_hash`) for password hashing
- Planned three auth features: set up password, change password, reset lost password
- Reset strategy for lost password TBD — likely admin reset or CLI script (no email for now)
- Agreed plan: finish full database schema next session, then implement auth/security

## 2026-04-14 (continued)
- Started writing schema.sql; completed `users` table
- `users` fields: `id`, `username`, `email`, `password_hash`, `rights`, `created_at`
- `rights` uses a CHECK constraint: values are `'admin'`, `'read_write'`, `'read_only'` — admin doubles as primary/household owner
- Decided against a `primary_id` self-referencing FK — unnecessary because one DB file = one household, so all users in the file are already associated
- No separate households table needed for this deployment model

## 2026-04-14
- Discussed financial API integration (Plaid, Teller.io); decided API is a post-v1 goal
- Designed transaction fields to align with standard API response objects for easier future integration
- Added `external_id` (provider's transaction ID), `api_category`, `pending`, `source`, and `import_date` fields to transactions table
- `import_date` records when a record entered the system — useful for debugging, auditing, and dedup

## 2026-04-13
- Defined project concept: free, self-hosted Mint replacement
- Chose tech stack: Python/Flask, SQLite, Pandas, ofxparse, Bootstrap
- Installed Python 3.12.3, pip, python3-venv, and project packages
- Installed VS Code with Python, Pylance, and SQLite Viewer extensions
- Created project folder at ~/projects/finance-tool
- Set up Python virtual environment
- Scaffolded initial project structure (app.py, folders, CLAUDE.md, requirements.txt)
- Confirmed Flask dev server running at http://127.0.0.1:5000
- Decided multi-user architecture: one SQLite file per household, small deployment (local/personal server, not SaaS)
- Users within a household can share accounts (e.g. spouses) or keep separate accounts
- Designed table list: users, accounts, account_members, statements, transactions, categories, categorization_rules
- Categories and rules are household-wide (shared between members)
- Security model: file permissions on DB files + strong login password; no encryption-at-rest required
- Established AI assistance rule: Claude is tutor/explainer, not code author — user writes the code
- Agreed: no separate chat log file; decisions captured in CLAUDE.md, milestones in PROJECT_LOG.md
