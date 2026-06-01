# Project Log — Personal Finance Tool

## 2026-05-31 (end of session)
- Rewrote `GET /transactions` route with per-field filters: `filter_account`, `filter_description`, `filter_merchant`, `filter_category`, `filter_suggested_category`, `filter_api_category`, `amount_min`, `amount_max`, `date_from`, `date_to`
- Added sort via `sort` and `direction` params — `elif` chain maps sort value to SQL column expression; `direction` whitelisted to `ASC`/`DESC` to prevent injection
- Amount min/max use `try/except float()` to safely convert string params to numbers
- All filter and sort values passed back to `render_template` for sticky form
- Added `filter_account` and `sort == 'account'` — both wired to `a.name` in the JOIN
- Started rewriting `transactions.html` — old single search form removed; new form wraps table; all 8 sort radio buttons added (Date, Account, Description, Merchant, Amount, Category, Suggested Category, Bank Category)
- Template mid-session state — still needed when resuming:
  - `</form>` is in wrong place (line 50) — must move to after `</table>`
  - `<div class="d-flex">` unclosed — needs `</div>` before `</form>`
  - Order (ASC/DESC) radio buttons not yet added after `Order:` label
  - Search and Clear buttons not yet added
  - `checked` attributes missing on all sort radios (stickiness)
  - Filter input row (`<tr>` in `<thead>`) not yet added
- Next: finish sort row (Order radios + buttons + checked attrs), then add filter input row in thead

## 2026-05-30 (end of session — continued)
- Agreed on CS50 completion feature list — documented in CLAUDE.md under "CS50 Feature Completion Plan"
- Decided to keep the stack JavaScript-free throughout; monthly summary will be a plain HTML table rather than a chart
- Post-CS50 phase will continue with greater AI support and additional features
- Added search/filter form to `transactions.html`: field dropdown (All/Description/Merchant/Category/Suggested Category/Bank Category), text search input, native HTML5 date range pickers (`<input type="date">`), Search and Clear buttons
- Used Bootstrap `d-flex gap-2` for inline layout; `form-select` on dropdown, `form-control` on inputs
- Decided to add date range filter after seeing native HTML5 date inputs work cleanly without JavaScript
- Built dynamic WHERE clause in `GET /transactions` route: reads `search`, `field`, `date_from`, `date_to` from `request.args`; builds `conditions` list and `params` list incrementally; joins with `AND`; interpolates into SQL f-string; passes params to `.execute()`
- Searching and date filtering tested and working
- Known issue: form is not sticky — inputs reset to blank on each search, so a second search loses previous filter values; fix is to pass filter values back to the template via `render_template` and set `value` attributes on inputs
- Next: fix sticky form (pass `search`, `field`, `date_from`, `date_to` to template; set `value` on inputs, `selected` on dropdown option)

## 2026-05-29 (end of session)
- Started building the transactions page
- Created `routes/transactions.py` Blueprint (`transactions_bp`) following the same pattern as `routes/upload.py`
- Removed stub `/transactions` route from `app.py`; registered `transactions_bp` in `app.py`
- Built `GET /transactions` route: auth guard (redirects to `/login` if not logged in), JOIN query across `transactions`, `accounts`, and `categories` (twice, aliased `c1`/`c2`), ordered by date descending, connection closed before return
- Query returns: date, `account_name` (aliased from `a.name AS account_name`), description, merchant_name, amount, category, suggested_category, api_category
- Added `uploads/` to `.gitignore` — contains real bank statement files, should not be committed
- Built `transactions.html` — Bootstrap striped table, loops over `transactions_display`, amount formatted to 2 decimal places with `"%.2f"|format()`, negative amounts colored red via `text-danger` conditional class, empty state handled with `{% else %}` on the for loop
- Transactions page tested and working — 988 rows loading correctly
- Decided on server-side sorting and filtering via GET params (no JavaScript) — sorting via `?sort=col&dir=asc`, search via `?search=term` with WHERE clause in SQL
- Next: add search form to `transactions.html`, then update route to read `request.args` and apply WHERE/ORDER BY

## 2026-05-25 (end of session)
- Tested full upload pipeline end to end — 988 transactions successfully imported
- Fixed three bugs found during testing:
  - `staging_transactions.dedup_hash` had a UNIQUE constraint that blocked within-file duplicates (e.g. two identical charges same day same vendor); removed UNIQUE from staging table — constraint kept on `transactions` table where it belongs
  - `DELETE FROM staging_transactions WHERE session_id = ?` used a freshly generated session_id so never deleted anything; changed to `DELETE FROM staging_transactions` (no filter); simultaneous upload race condition accepted as a known v1 limitation
  - `session['duplicate_count'] = duplicate_count` stored a Pandas `int64` which Flask's JSON session serializer can't handle; fixed with `int(duplicate_count)`
- Upload pipeline is now fully working: parse → normalize → deduplicate → stage → review → commit

## 2026-05-24 (end of session)
- Built `/upload/review` GET+POST route in `routes/upload.py`
  - GET: loads `staging_transactions` into DataFrame with `pd.read_sql_query`, drops internal columns (`session_id`, `account_id`, `dedup_hash`, `source`, `import_date`, `statement_id`, `pending`), reads `duplicate_count` from session, renders `review.html`
  - Decided to keep `id` column visible — will be useful as a reference when row-level selection is added in the future
  - POST: uses `INSERT INTO ... SELECT` to move rows directly from staging to transactions (no Python loop), uses `result.rowcount` for flash message count, deletes staging rows, commits, redirects to `/transactions`
- Updated `upload_process`: stores `duplicate_count` in session, redirects to `/upload/review` instead of rendering directly
- Updated `review.html` form action from `/upload/commit` to `/upload/review`
- Deleted `data/` folder and `registry.db` to reset for testing after staging_transactions schema change

## 2026-05-22 (end of session)
- Added duplicate detection in `upload_process`: queries existing `dedup_hash` values from transactions table, flags duplicates, counts them, flashes warning if any found, drops them from dataframe
- Added `duplicate_count` tracking before drop so user is informed of skipped rows
- Changed end of `upload_process` to `render_template('review.html', ...)` passing `transactions=df.to_dict('records')` and `duplicate_count` — review template not yet built
- Identified need to drop `is_duplicate` column before passing df to template
- Open question: how to pass transactions from review page to commit route — options are session storage, re-processing, or hidden form fields; not yet decided
- Next: decide on commit approach, build `review.html`, build `/upload/commit` route

## 2026-05-23 (end of session — continued)
- Built `review.html` — displays staged transactions in a striped table with duplicate count warning, Confirm Import and Cancel buttons
- Decided `/upload/review` will be a GET route that reads from `staging_transactions` into a dataframe and passes it to the template
- Updated `upload_process` to write to `staging_transactions` using `session_id` before rendering review
- Added staging table cleanup at start of `upload()` — clears all stale staging rows before new upload begins
- Fixed `DELETE * FROM staging_transactions` → `DELETE FROM staging_transactions`
- Next: build `/upload/review` GET route and `/upload/commit` POST route

## 2026-05-23 (end of session)
- Decided on `staging_transactions` table approach for review-to-commit handoff:
  - Permanent table in household DB with `session_id` column to identify the current upload
  - `upload_process` writes normalized rows to `staging_transactions` after dedup
  - `review.html` reads from `staging_transactions` for display
  - `/upload/commit` moves rows from staging to transactions, then deletes staging rows
  - Stale rows cleared at start of `upload_process` in case of previous abandoned upload
  - Cancel button deletes staging rows without committing
- Next: add `staging_transactions` to `schema.sql`, then build `review.html` and `/upload/commit` route

## 2026-05-21 (end of session — continued)
- Completed dedup hash: `make_dedup_hash()` function hashes account_id, date, description (stripped/lowercased), and amount using SHA256; applied to full dataframe with `df.apply()`
- Wired up `upload_process` — changed to `methods=['GET', 'POST']` and `upload_confirm` now redirects to `/upload/process`
- Fixed 32 rows in Chase test CSV where `&amp,` was splitting descriptions across columns; saved fixed file as `Chase9887_Activity20250101_20251231_20260508-m.csv` in `transactions/`
- Tested full upload pipeline end to end — file validation, column mapping, normalization, and dedup hash all running; added temporary `redirect('/upload')` at end of `upload_process` as placeholder
- Next: build review step (show user preview of what's about to be committed), then database insert

## 2026-05-21 (end of session)
- Philosophy discussion on categorization: decided to move user categorization confirmation to post-import rather than blocking the import flow; rules engine will populate `suggested_category_id` at import time
- User proposed three distinct category fields to avoid overwriting data: `api_category` (bank's label), `suggested_category_id` (rules engine guess), `category_id` (user confirmed)
- Added `suggested_category_id INTEGER` to transactions table — FK to `categories(id)` with `ON DELETE SET NULL`, consistent with existing `category_id`
- Note: existing test DBs need to be deleted and recreated to pick up schema change
- Next: dedup hash, then wire up `upload_process`

## 2026-05-20 (end of session)
- Added account selection to `upload.html` — dropdown of existing accounts with "Add Account" button to the right using Bootstrap `d-flex`
- Built `/accounts/new` route in `app.py` (GET + POST) — validates all fields, inserts into household DB, redirects to `/accounts` on success
- Built `add_account.html` template — fixed `{% block main %}`, action points to `/accounts/new`, account_type options match schema CHECK constraint (`checking`, `savings`, `credit`, `investment`, `other`)
- Added account query to upload GET handler in `routes/upload.py` — fetches accounts from household DB and passes to template
- Added `account_id` validation to upload POST handler — reads from form, checks before file save, stores in session
- Fixed form field mismatch in `add_account.html`: `name="name"` → `name="account_name"` to match `request.form.get('account_name')` in the route
- Tested end to end — account creation and upload account selection working
- Next: complete dedup hash now that `account_id` is available in session; then wire up `upload_process`

## 2026-05-17 (end of session — continued)
- Completed normalization logic in `upload_process()`:
  - Fixed ignore column drop: replaced loop with `df.drop(columns=['ignore'], errors='ignore')`
  - Added currency stripping (`[$,]`) on `amount`, `debit`, and `credit` columns before any math
  - Fixed `float(df[col])` → `pd.to_numeric(df[col])` — `float()` works on single values, not columns
  - Debit/credit combine now works correctly since columns are already numeric before the `df.apply()` call
- Started deduplication design — identified that `account_id` is required in the dedup hash to distinguish transactions across different bank accounts
- Identified design gap: user has no way to select an account during upload yet
- Decision: add account selection to `upload.html` — dropdown of existing accounts plus inline "Add new account" option; this must be done before dedup hash can be completed
- Next: add account selection to `upload.html` and wire `account_id` through the session into the dedup hash

## 2026-05-17 (end of session)
- Improved `upload_process()` error messages: replaced hardcoded `row.iloc[0]` and `row.iloc[1]` with mapping-aware `date_col` and `desc_col` lookups; errors now show column name, row number, bad value, plus the row's date and description for context
- Added `pd.isna(value)` skip for debit/credit columns — empty cells are valid since a row will only have one or the other
- Decided to use `df.rename()` to map bank column names to database field names rather than building a list of dicts — stays in Pandas, more efficient, cleaner for normalization step
- Decided against adding `post_date` to the schema — both `transaction_date` and `post_date` will map to the `date` field; keeping schema simple
- Wrote `df.rename(columns={df.columns[int(k)]: v for k, v in mapping.items()})` to rename columns using the confirmed mapping
- Identified normalization tasks for next session:
  - Combine `debit`/`credit` columns into signed `amount`
  - Rename `transaction_date`/`post_date` → `date`
  - Rename `category` → `api_category`
  - Drop ignored columns
  - Parse dates with `pd.to_datetime()`
  - Strip whitespace from descriptions with `.str.strip()`
- Next: implement normalization, then deduplication, then wire up `upload_process` to be reachable

## 2026-05-16 (end of session — continued)
- Fixed two auto-guess bugs in `confirm.html` (lines 20-21): `'trans' and 'date' in header.lower()` was incorrect — `'trans'` alone is always truthy; corrected to `'trans' in header.lower() and 'date' in header.lower()`; same fix for `post_date`
- Decided to keep the generic `Date` dropdown option alongside `Transaction Date` and `Post Date`: browser's "last `selected` wins" behavior means the more specific options naturally take priority when headers contain both keywords — no extra exclusion condition needed
- Fixed `upload_confirm()` validation: accepts `date` or `transaction_date` as a valid date mapping; `post_date` alone is not sufficient — user confirmed this is the correct requirement
- Upload pipeline tested through Step 2; `upload_confirm()` route working
- Next: Step 3 — column validation (read full file with confirmed mapping; reject on any unparseable date or amount with row number, column, and value found)

## 2026-05-16 (end of session)
- Built `upload_process()` route (Step 3 — column validation) in `routes/upload.py`
  - Reads full CSV with `pd.read_csv(file_path)` once at top
  - Iterates `mapping.items()` for date columns (`date`, `transaction_date`, `post_date`) and validates each value with `pd.to_datetime()`
  - Iterates `mapping.items()` for amount/debit/credit columns and validates each value with `float()`
  - Uses `enumerate(..., start=2)` to track row numbers (offset by 1 for header row)
  - Uses `int(column_index)` to handle session key string conversion
  - Error flash includes row number, column index, and bad value
- Next session:
  - Improve error messages: replace column index number with column name (`df.columns[int(column_index)]`); include the transaction date and description alongside the bad value so the user can locate the row in their bank export
  - Wire up `upload_process` — needs a form or redirect from `upload_confirm` to actually be reachable

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
