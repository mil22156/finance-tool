# Project Log — Personal Finance Tool

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
- Initialized git in ~/projects/, set global user.email and user.name
- Push to GitHub blocked — GitHub requires a personal access token (not password) for HTTPS auth
- Next step: generate PAT at GitHub → Settings → Developer Settings → Personal Access Tokens (classic), repo scope, then retry push
- After projects repo is pushed, need to init and push finance-tool repo separately

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
