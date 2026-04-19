# AI Assistance Journal

This file documents contributions made by Claude (claude-sonnet-4-6) via Claude Code
to the CS50x Final Project — Personal Finance Tool.

As required by CS50x academic honesty policy, all AI assistance is cited here.

---

## Session 1 — 2026-04-13

### Project Planning
- Discussed and defined the project concept: a free, self-hosted Mint replacement
  for uploading bank/credit card statements with deduplication and categorization
- Proposed the core application flow: upload → parse → normalize → deduplicate →
  categorize → review → commit
- Recommended tech stack: Python + Flask, SQLite, Pandas, ofxparse, Jinja2 + Bootstrap
- Designed the initial database schema (accounts, statements, transactions, categories,
  category_rules tables) including the dedup_hash approach for deduplication
- Proposed the project folder structure

### Environment Setup
- Diagnosed missing python3-venv package and provided fix
- Verified virtual environment creation and package installation
- Verified Flask 3.1.3, Pandas 3.0.2, ofxparse 0.21 installed correctly

### Project Scaffolding
- Created project folder structure (database/, parsers/, core/, templates/, static/)
- Created initial app.py (Flask entry point)
- Created CLAUDE.md (project context file)
- Created requirements.txt

---

## Session 2 — 2026-04-14

### Database Schema Design
- Discussed transaction field design; proposed aligning fields with financial API providers
  (Teller.io, Plaid) for easier future integration — `external_id`, `api_category`, `pending`,
  `source`, `import_date`
- Advised that API integration should be a post-v1 goal; import pipeline designed so API
  is just another source feeding the same flow
- Reviewed and gave feedback on `users` table written by user:
  - Flagged incorrect SQLite types (`SERIAL`, `VARCHAR`, `TIMESTAMP`) and explained correct equivalents
  - Suggested CHECK constraint for `rights` field: `CHECK(rights IN ('admin', 'read_write', 'read_only'))`
  - Advised against `primary_id` self-referencing FK — unnecessary given one-DB-per-household model
  - Explained that `admin` role covers the "primary user" concept, removing need for a separate field

### Authentication Design
- Recommended Werkzeug (`generate_password_hash` / `check_password_hash`) for password hashing
- Explained the three auth use cases: set up, change, and reset password
- Noted that password reset strategy needs decision (no email in self-hosted model)
- Advised finishing schema before writing auth code

### VS Code / Tooling
- Advised installing `alexcvzz` SQLite extension for SQLite-aware autocomplete and DB browsing
- Diagnosed missing `sqlite3` binary causing extension error; fix: `sudo apt install sqlite3`

### Documentation
- Updated PROJECT_LOG.md, CLAUDE.md, and AI_JOURNAL.md to reflect decisions made this session

---

## Session 3 — 2026-04-17

### Database Schema — accounts table
- Reviewed Copilot-suggested `accounts` table; explained that the `user_id` FK Copilot added was incorrect — accounts are household-level, not user-level, per the one-DB-per-household design; user↔account relationships belong in `account_members`
- Identified trailing comma syntax error left by Copilot after FK removal

### Database Schema — account_members table
- Explained junction table concept and how it links users to accounts with a role
- Explained composite primary keys vs single-column PKs
- Explained ON DELETE CASCADE and recommended it for this design
- Reviewed several drafts; flagged: incorrect `primary_key TEXT PRIMARY KEY` column, duplicate PRIMARY KEY declarations, wrong constraint ordering
- User wrote final correct version independently after feedback

### Database Schema — categories and categorization_rules tables
- Explained self-referencing FK for parent_id in categories table
- Discussed categorization_rules design: suggested adding field-specific pattern columns (description, merchant, source) so rules can match on multiple fields
- Explained table-level CHECK constraint to enforce at least one pattern field is non-NULL
- Discussed priority ordering and suggested leaving gaps (10, 20, 30) for easy insertion; noted sorting algorithms can be explored later for the rules UI
- Advised RESTRICT on category FK delete — safer than CASCADE, can be changed later

### GitHub Setup
- Created .gitignore file for the project
- Advised public repo is fine since no financial data is stored in the repo
- Suggested master `projects` index repo with README linking to individual project repos
- Created README.md for master projects index repo
- Walked user through git init, global config, remote setup, and PAT authentication
- Installed GitHub CLI and authenticated; pushed both repos to GitHub
- Created CLAUDE_CONTEXT.md for persistent Claude.ai context

### Security Review (prompted by Claude.ai)
- Reviewed four security areas: password hashing, path traversal, SQL injection, dedup hash
- Identified missing `dedup_hash` column in transactions table — confirmed as oversight
- Explained purpose of deduplication hash and why a database index speeds up lookups
- Walked user through adding `dedup_hash` column and `CREATE INDEX` statement
- Path traversal and SQL injection to be addressed as application code is written

### Database Schema — statements table
- Confirmed FK constraints enforce referential integrity at the DB level (not just Python)
- Reviewed and gave feedback on statements table: flagged missing `account_id` column declaration, incorrect CHECK constraint syntax, unsupported file types (pdf/xlsx)

### Database Schema — transactions table
- Explained `external_id` field purpose (future API deduplication)
- Clarified SQLite BOOLEAN type (accepted but stored as INTEGER internally)
- Confirmed nullable FK is valid SQL — user added `statement_id` as nullable FK to trace transactions to source statement
- Reviewed and gave feedback: flagged `category_ID` typed as TEXT instead of INTEGER, duplicate `category TEXT` column, `note` vs `notes` naming inconsistency

### GitHub Setup
- Advised creating private repo for financial data
- Outlined git init → add → commit → remote → push steps
- Flagged need for .gitignore to exclude venv/ and *.db files before first push

### Documentation
- Updated PROJECT_LOG.md and AI_JOURNAL.md to reflect decisions made this session

---

## AI Usage Policy (established 2026-04-13)

Two AI tools are in use on this project:

**Claude Code (claude-sonnet-4-6)**
- Role: tutor, explainer, code reviewer, debugger, project tracker
- Does NOT write production code for the project
- All assistance logged in this journal by session

**GitHub Copilot (Grok Code Fast 1)**
- Role: inline code suggestions while typing in VS Code
- Used like autocomplete — user decides what to accept
- Any significant Copilot-generated code should be noted in this journal

---

_This journal is updated by Claude Code at the end of each working session._
