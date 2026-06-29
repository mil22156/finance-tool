# Household Finance Tool

#### Video Demo: <ADD YOUR UNLISTED YOUTUBE URL HERE>

#### Description

Household Finance Tool is a free, self-hosted personal finance application — a lightweight replacement for services like Mint, built for people who would rather keep their financial data on their own machine than hand it to a third party. Users upload bank and credit-card statements, and the application parses, deduplicates, and categorizes each transaction so that spending can be reviewed and summarized. All data stays local: there are no external services, no API calls, and nothing leaves the computer it runs on.

The tool is designed for a small number of households (for example, a couple of families sharing a personal server) rather than as a large commercial service. Each household gets its own isolated SQLite database file, and members of a household can either share accounts or keep them separate. Within a household, users log in with a hashed password, upload statements, assign categories, and view a monthly summary of where their money went.

A typical workflow is: upload a statement → the file is validated → columns are mapped and confirmed → every row is validated → duplicates are removed → categories are suggested → the user reviews the staged transactions → the data is committed to the database. From there the user can filter and sort transactions, assign categories manually or in bulk, and let the rules engine suggest categories automatically on future imports.

## Features

- **Upload pipeline** with a strict three-step validation gate (file check, column mapping, row validation) before any data is written.
- **Deduplication** using a SHA-256 hash of account, date, amount, and normalized description, so re-uploading an overlapping statement does not create duplicate records.
- **Transactions page** with per-column filters, sorting, date ranges, and amount ranges.
- **Categories management** (create, edit, delete) and both single and bulk category assignment.
- **Auto-categorization rules** that learn from how transactions are categorized and suggest categories on import.
- **Monthly summary** that totals spending by category for any filtered date range.

## File Structure

- `app.py` — the Flask entry point. Sets up the application, registers the route blueprints, and handles login, logout, household creation, and user management.
- `database/schema.sql` — the schema for a household database (users, accounts, transactions, categories, rules, and a staging table for in-progress uploads).
- `database/registry_schema.sql` — the schema for the small registry database that maps household names to their database files.
- `database/db.py` — helper functions that open database connections, enable foreign-key enforcement, and initialize databases.
- `routes/upload.py` — the upload pipeline: parsing CSV statements with pandas, building dedup hashes, staging rows, computing suggested categories, and committing reviewed transactions.
- `routes/transactions.py` — the transactions list with filtering and sorting, the single-transaction edit form, and bulk category assignment.
- `routes/categories.py` — category CRUD and the default-category seeding function.
- `routes/summary.py` — the monthly summary report, an aggregate query grouped by category.
- `core/categorizer.py` — the rules engine (`category_rule_check`), which records and looks up "description → category" rules.
- `core/auth.py` — password hashing and verification.
- `templates/` — Jinja2/Bootstrap templates for every page.
- `static/` — CSS and favicon.

## Design Decisions

I chose **one SQLite file per household** instead of a single shared database because it gives strong data isolation with almost no extra code — one family's data physically cannot appear in another's queries. A small registry database maps household names to their files at login.

For **deduplication**, I hash account, date, amount, and a normalized description rather than trusting any single bank-provided ID, because CSV exports rarely include stable transaction IDs. The hash is stored with a unique index so duplicate detection is fast at import time.

For **categorization**, rules match on the full description with an exact match rather than partial matching. This avoids false positives, and when a new categorization conflicts with an existing rule, the user is explicitly asked whether to overwrite the rule or keep it. The bank's own suggested category is stored separately and never trusted by default.

The **upload validation gate** is deliberately strict: a single unparseable value rejects the whole upload with a specific error, which keeps bad data out of the database.

## How to Run

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000. Creating a household requires a `CREATION_CODE` set in a `.env` file.

## AI Assistance

Claude Code was used as a tutor, explainer, and code reviewer during development; the assistance provided in each session is documented in `AI_JOURNAL.md`.
