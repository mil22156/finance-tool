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

## CS50 Submission
- Deadline: December 31, 2026
- Submit via: submit50 cs50/problems/2026/x/project
- Requires: README.md, ≤3 min YouTube video, code submission
