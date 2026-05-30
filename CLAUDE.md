# Finance Tool — CLAUDE.md

## Project Summary
A free, self-hosted personal finance tool (Mint replacement). Users upload bank and
credit card statements, transactions are parsed, deduplicated, and categorized.

## Stack
- Python 3.12 + Flask 3.1
- SQLite (local database)
- Pandas (CSV parsing and deduplication)
- ofxparse (OFX/QFX statement parsing)
- Jinja2 + Bootstrap (frontend)

## Project Structure
```
app.py              — Flask entry point
database/
  schema.sql        — Database schema
parsers/
  csv_parser.py     — CSV statement parser
  ofx_parser.py     — OFX/QFX statement parser
core/
  deduplicator.py   — Deduplication logic
  categorizer.py    — Rules-based categorization engine
templates/          — Jinja2 HTML templates
static/             — CSS and JS
```

## Key Design Decisions
- All data stays local — no external services
- Deduplication uses a hash of (account + date + amount + normalized description)
- Categorization is rules-based with user override capability
- Statement upload goes through: parse → normalize → deduplicate → categorize → review → commit
- Upload pipeline uses a strict 3-step validation gate before any data is written (decided 2026-05-10):
  - **Step 1 — File validation:** check extension/MIME type, file size limit, non-empty; for OFX/QFX also validate header structure; hard reject with clear error message
  - **Step 2 — Column mapping:** parse headers + ~5 sample rows; auto-guess mapping from column names; render a preview table where each column header is a dropdown (Date / Description / Amount / Debit / Credit / Ignore); user confirms or corrects before proceeding
  - **Step 3 — Column validation:** with mapping confirmed, validate every row; any unparseable value (bad date, non-numeric amount) rejects the entire upload with a specific error (row number, column, value found); start strict and relax rules only if real usage demands it
- Mapping profile persistence (saving a bank's column layout for re-use) is a post-v1 goal
- File is held between Step 1 and Step 2 via Flask session (`session['uploaded_file']`)
- Staging between Step 2/3 and commit uses a permanent `staging_transactions` table in the household DB with a `session_id` column; rows are cleared at upload start (in case of prior abandoned upload), after commit, and on cancel

## Multi-User Architecture (decided 2026-04-13)
- Target deployment: small number of users (2-5 households), local machine or personal server — NOT a SaaS
- **One SQLite database file per household** (e.g. `household_abc123.db`) for strong data isolation
- A small `registry.db` or config file maps household names to their database file paths (used at login)
- Within each household database, users can share accounts (e.g. spouses) or keep separate accounts
- **`users`** table: members of the household, with hashed passwords; `rights` column uses CHECK constraint (`'admin'`, `'read_write'`, `'read_only'`) — admin is the household owner/primary user
- **`accounts`** table: bank/credit card accounts
- **`account_members`** junction table: many-to-many users↔accounts, with a `role` column (owner/member)
- **`statements`** table: uploaded files, linked to an account, tracks date range and import timestamp
- **`transactions`** table: central table, linked to account; includes raw description, cleaned merchant, category, notes; designed to align with financial API response fields (see Transaction Fields below)
- **`categories`** table: household-wide, optional parent for nesting
- **`categorization_rules`** table: household-wide rules (e.g. "WHOLE FOODS → Groceries"), ordered by priority
- Categories and rules are shared across all members of a household
- Security model: file permissions (chmod 600) on database files; strong login password sufficient for this threat model
- **Household creation gate (decided 2026-05-03):** `/household/new` requires a `CREATION_CODE` stored in a `.env` file (excluded from git); Flask reads it via `os.environ.get()` at startup; submitted code is checked against it on POST — if it doesn't match, the request is rejected; code can be changed or removed after initial setup

## Transaction Fields (decided 2026-04-14)
Designed to align with financial API providers (Teller.io, Plaid, etc.) for easier future integration:
- `id` — internal primary key
- `account_id` — FK to accounts table
- `external_id` — provider's transaction ID (for deduplication against future API syncs)
- `date` — posted date
- `amount` — positive/negative per provider convention
- `description` — raw bank description string
- `merchant_name` — cleaned merchant name (from API or user-defined)
- `category_id` — FK to categories table (user's own categorization)
- `api_category` — raw category suggestion from API (stored separately, not trusted by default)
- `pending` — boolean, whether transaction is settled or still pending
- `notes` — user notes
- `source` — how the record entered the system (e.g. 'csv', 'ofx', 'api', 'manual')
- `import_date` — timestamp of when the record was imported into the system
- `dedup_hash` — SHA256 hash of (account_id + date + amount + normalized description); NOT NULL UNIQUE; indexed via `idx_transactions_dedup_hash` for fast import-time deduplication lookups
- `statement_id` — nullable FK to statements table; traces a transaction back to its source upload file
- API integration is a post-v1 goal; import pipeline should be designed so API is just another source feeding the same normalize → deduplicate → categorize flow

## Documentation Discipline
- **At the end of every session, or whenever a significant decision is made**, update PROJECT_LOG.md with a dated entry and update the relevant sections of this file if anything architectural changed
- PROJECT_LOG.md = milestone notes and decisions by date
- CLAUDE.md = stable reference: architecture, constraints, guidelines
- Pay special attention to capturing decisions here — do not let context drift between sessions

## Dev Commands
```bash
source venv/bin/activate
python app.py        # start dev server at http://127.0.0.1:5000
```

## AI Assistance Guidelines
- Claude Code role: tutor, explainer, reviewer, debugger — NOT code author
- GitHub Copilot role: inline suggestions while typing (user decides what to accept)
- Any significant Copilot-generated code must be logged in AI_JOURNAL.md
- **Claude Code must update AI_JOURNAL.md whenever PROJECT_LOG.md is updated**, logging what assistance was provided (explanations, design suggestions, feedback, debugging) — this journal documents AI contributions for CS50 academic honesty purposes
- Work through problems step by step; let the user write the code
- Flag if any assistance seems to cross the line for CS50 academic honesty
- User will also flag if things feel like too much automation
- When in doubt, explain the concept and let the user implement it
- When running git commands, briefly explain what each command is doing and why

## CS50 Feature Completion Plan (agreed 2026-05-30)
Features required to call the project complete for CS50 submission, in build order:
- [x] Upload pipeline — parse → deduplicate → stage → review → commit (done 2026-05-25)
- [x] Transactions list page — JOIN query, Bootstrap table, amount formatting (done 2026-05-29)
- [ ] Transactions sort and filter — server-side via GET params, no JavaScript
- [ ] Accounts list page — simple list of household accounts
- [ ] Categories management — CRUD UI for creating and editing categories
- [ ] Manual category assignment — assign `category_ID` to a transaction from the transactions page
- [ ] Auto-categorization rules — rules engine runs at import time, populates `suggested_category_id`; CRUD UI for managing rules
- [ ] Monthly summary table — totals by category by month, pure SQL aggregation, no JavaScript
- [ ] README.md
- [ ] Video (3 min, unlisted YouTube)

## Before We Finish (Pre-submission To-Do)
- [ ] Decide on a permanent data directory location — currently `data/` is relative to the project folder; revisit if deployment needs change
- [ ] Harden household creation code — currently a plain secret stored in `.env`; consider expiring codes, rate limiting, or admin-only creation for stricter deployments
- [x] Refactor upload logic into a Flask Blueprint (`routes/upload.py`) — done 2026-05-10

## CS50 Submission
- Deadline: December 31, 2026 at 23:59 UTC — all three steps must be complete by then

### Step 1: Video
- Max 3 minutes
- Must open with: project title, your name, GitHub username, edX username, city and country, recording date
- Upload to YouTube as **unlisted** (not private)
- Submit the URL via forms.cs50.io
- **Video tools:** OBS Studio (screen recording) + Shotcut (editing) — both installed; make the video last, once the project is complete

### Step 2: README.md
- File must be named exactly `README.md`, placed at the root of the project directory
- Target ~750 words minimum
- Must include: project title, YouTube URL from Step 1, description of the project, explanation of each file and its purpose, design choice rationales
- Submit via: `submit50 cs50/problems/2026/x/project` (uses GitHub credentials)
- Keep submission under 100MB

### Step 3: Verify
- Visit cs50.me/cs50x a few minutes after submitting to confirm completion and trigger certificate generation

### AI Tool Policy
- AI tools are permitted but must be cited — the official requirement is **code comments** (AI_JOURNAL.md covers the spirit of this, but also add inline comments where AI materially contributed to specific code)
