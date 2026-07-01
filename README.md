# Household Finance Tool

> **Note:** This is the version of the app as submitted for Harvard CS50x (final project) in June 2026, tagged `cs50-submission`. Any later commits are post-submission changes.

#### Video Demo: (https://youtu.be/1YAl1KN5CW8)

#### Description

Household Finance Tool is a free, self-hosted lightweight replacement for services like Mint, built for people who would rather keep their financial data on their own machine than hand it to a third party or want direct control over the function of the softwary. Users upload bank and credit-card statements, and the application parses, deduplicates, and categorizes each transaction so that spending can be reviewed and summarized. All data stays local and nothing leaves the computer it runs on.

The tool is designed for a small number of households rather than as a web based commercial site. Each household gets its own isolated SQLite database file, and members of a household can either share accounts or keep them separate. Within a household, users log in with a hashed password, upload statements, assign categories, and view a monthly summary of where their money went.

A typical workflow is: 
1. upload statement
2. validate file 
3. map statement columns 
4. duplicates of existing transactions from the database are removed 
5. categories are suggested based on the previous choices in the existing database
6. user reviews the data befor upload
7. data is committed to the transactions table.
8. transactions can be edited manually from the transactions page


Features
The work to get just these features working was a lot more than anticipated at the beginning of the project so this is somewhere close to the minimum feature set to get it working. Since this is an open source project, others can add features they would desire.

-Upload - with a strict three-step validation gate (file check, column mapping, row validation) before any data is written.
-Deduplication - using a SHA-256 hash of account, date, amount, and normalized description, so re-uploading an overlapping statement does not create duplicate records.
-Transactions Page - with per-column filters, sorting, date ranges, and amount ranges.
-Category management - (create, edit, delete) and both single and bulk category assignment.
-Auto-categorization rules - that learn from how transactions are categorized and suggest categories on import.
-Monthly summary - that totals spending by category for any filtered date range.

File Structure

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

How to Run

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000. Creating a household requires a `CREATION_CODE` set in a `.env` file.

AI Assistance

Claude Code was used as a tutor, explainer, and code reviewer during development; the assistance provided in each session is documented in `AI_JOURNAL.md`.

Some auto-complete from vs-code was used in the beginning of the project but this proved somewhat unreliable and it was unclear how this fit in with the guidance for the project so this was turned off.

Some code snippets were taken from Claude code where I was just not getting it but generally all the code was entered by me manually though granted with a lot of consultation with AI. This project would have gone a lot faster if Claude were actually writing the code but I didn't gather that that was in the spirit of the project so I did not do this.

I had AI do the draft of this readme file and I edited it. During the project I also had Claude draft the MD files with my approval. I also had Claude do the github commits.
