# Project Log — Personal Finance Tool

## 2026-06-30 (PROJECT COMPLETE — CS50x submitted)
- **Submitted the CS50x final project and received the course certificate.** 🎓
- Uploaded the demo video to YouTube (unlisted): https://youtu.be/1YAl1KN5CW8; added the URL to the README
- Submission logistics (for future reference): local `submit50` kept failing GitHub auth because its interactive credential prompt wasn't reaching the terminal; the working path was (1) `git push` with a personal access token via `credential.helper store`, which both updated GitHub and stored the token, then (2) submitting from **cs50.dev** — because `git` is disabled there, pulled the repo as a tarball (`wget .../main.tar.gz`) and ran `submit50` in the extracted folder
- Also learned mid-way that all prior commits were local only — GitHub `origin` was far behind until this session's push (commits ≠ pushes)
- Tagged this commit `cs50-submission` and added an "as submitted" note to the README so the submission snapshot stays identifiable as the repo evolves
- Final feature set as submitted: multi-user households, upload pipeline, transactions list w/ filter+sort, categories CRUD, manual + bulk categorization, auto-categorization (engine + import-time suggestions + edit-route conflict/overwrite), monthly summary. Rules CRUD UI was descoped.

## 2026-06-29 (end of session)
- Added the `/summary` nav link to layout.html
- Recorded the project video (OBS); to be uploaded to YouTube as unlisted
- Created a ~750-word draft `README.md` covering all CS50 requirements (title, video URL placeholder, description, features, file-by-file explanation, design rationale, run instructions, AI-assistance citation) — Claude drafted it at the user's request after the user distinguished prose-drafting from the no-code-authoring rule; user will heavily edit it
- Accuracy note for the README edit: `parsers/` is empty and there is no `core/deduplicator.py` despite CLAUDE.md describing them — CSV parsing and dedup-hash logic actually live inline in `routes/upload.py`; the draft was written to match the real repo. OFX/QFX is only a dependency, not wired — draft describes CSV upload only
- Remaining for CS50: finish editing README (in user's own voice, especially Design Decisions), add YouTube URL, upload video, submit via submit50, verify at cs50.me

## 2026-06-28 (end of session)
- **Descoped the rules CRUD UI** (out of project time budget) — auto-categorization is considered done; rules are created/changed via transaction edits only. Marked the CS50 plan item complete with this note
- Built the **monthly summary** as a category-totals report that reuses the transactions page's filter/sort UX (user's preferred design over a fixed month pivot) — the "monthly" view comes from setting the date filter to a month
- New `routes/summary.py` (`summary_bp`, registered in app.py); `GET /summary` reuses the transactions filter-building pattern (date range, account, category) and runs an aggregate query: `SELECT c1.name, SUM(t.amount) AS total, COUNT(*) AS cnt ... GROUP BY c1.name ORDER BY total`
- New `templates/summary.html` — filter form + grouped totals table (modeled on transactions.html)
- Bugs fixed during the build: blueprint name collision (`'categories'` → `'summary'`), `household_db_path` typo, `flash` missing comma, non-aggregate SELECT/invalid `ORDER BY ... SUM`, `render_template` positional args, the `sql=` assignment accidentally nested inside the `else` block (parsed fine but would NameError whenever a filter was applied), account filter operator, and a missing `{% endfor %}` in the template
- Verified rendering in the browser
- Known gaps (minor): no `/summary` nav link in layout.html yet; summary table still has empty Date/Account columns to tidy; no Apply button (Enter submits)
- Remaining for CS50: README.md, then the video

## 2026-06-27 (end of session)
- Built the conflict-overwrite UI for the transaction edit route — the last interactive piece of auto-categorization besides the rules CRUD page
- Edit route POST now has two phases distinguished by the `rule_action` form field: (1) initial save — resolve category, update transaction + commit (no conflict) or, on conflict, re-render the form with `conflict=True` committing nothing; (2) conflict resolution — both Overwrite and Leave update the transaction, Overwrite also calls `category_rule_check(..., overwrite=True)`
- Design decision (user's call): on conflict, commit nothing until the user chooses, so the Cancel link genuinely cancels — the transaction is updated in phase 2 by either button, not pre-committed in phase 1
- Buttons distinguished by their own `name="rule_action"`/`value` (overwrite/leave) rather than a hidden field — only the clicked submit button's name/value is sent
- transactions_form.html: category `<select>` swapped for a read-only box during conflict, plus an informative warning naming the existing vs proposed category ("currently categorized as X… categorize future as Y, or leave as-is?"); route passes `existing_category` (looked up from the rule's category_id) and `new_category` names
- Removed a stray duplicate hidden `new_category_id` input
- Verified working in the browser
- Next: rules CRUD UI (the only remaining piece to fully check the CS50 auto-categorization box), then monthly summary, README, video

## 2026-06-26 (end of session)
- Implemented import-time auto-categorization in `routes/upload.py` — the headline of the CS50 auto-categorization feature
- Threaded `suggested_category_id` through all four points of the upload pipeline: (1) compute at categorize step — load all `categorization_rules` into a dict once, then `rules.get(description)` per row (in-memory, one query, no per-row DB hit per the 06-12 design); (2) added `suggested_category_id` column to `staging_transactions` (schema.sql + `ALTER TABLE` on the live DB, since schema.sql doesn't touch existing files); (3) staging INSERT; (4) final commit INSERT (staging → transactions, both column list and SELECT)
- Used `dict.get()` rather than pandas `.map()` so misses return `None` (→ SQL NULL) instead of `NaN` (→ float)
- Review page now LEFT JOINs `categories` to display the category name instead of the raw `suggested_category_id`; review.html builds its table generically from the df so no template change needed (name-display fix unverified until next import)
- Populated `categorization_rules` from existing categorizations via a one-off SQL INSERT…SELECT (not app code): one rule per distinct categorized description, majority category wins per description (resolved the lone conflict, `EBLEN SHORT STOP #7`, to GROCERIES 33× over CARS/GAS 8×), skipped descriptions that already had a rule. 160 rules total, no duplicates. Backed up the DB first (`*.db.bak-<timestamp>`)
- Verified end-to-end on a real import: suggestions populated on the review page and persisted to `transactions`
- Git hygiene note: the `.db.bak-*` backup is NOT matched by the `*.db` gitignore rule, so `data/` shows as untracked — must never `git add data/`/`git add .`; also a stray empty `schema.sql` at repo root (and earlier an empty `data/<household>.db`) are accidental artifacts to delete
- Next: rules CRUD UI (manage `categorization_rules`); conflict-overwrite UI in the edit route (still a TODO); then the CS50 auto-categorization checkbox is fully done

## 2026-06-24 (end of session)
- Wired `category_rule_check` into the `POST /transactions/edit/<id>` route — editing a transaction's category now also creates/matches a categorization rule, sharing the route's connection so the transaction UPDATE and the rule write commit together
- Confirmed (per the 06-12 design) the rules function does NOT belong in the upload/import pipeline — that path will use the in-memory dict batch lookup; the function only serves assignment paths (edit, bulk assign). Briefly started toward the upload route before catching this
- Fixed the latent `fetchone()[0]` bug at the category lookup: split into fetch row → `if row is None` guard → `row[0]`, so a missing category no longer raises `TypeError` before the guard runs
- Wrapped the `category_rule_check` call in `try/except ValueError` (closes the connection and flashes on failure), though the inputs are validated upstream so it shouldn't fire in practice
- Conflict case (rule already maps the description to a different category) left as an explicit TODO — function returns the existing id as the signal; plan is to reuse the bulk-assign inline-confirm pattern to offer keep/overwrite, deferred to its own task
- Not yet verified by running the app
- Next: run the app and confirm a rule lands in `categorization_rules`; then conflict-overwrite UI; then rules CRUD page; then import-time batch lookup

## 2026-06-21 (end of session)
- Implemented `category_rule_check(db, description, category_id, overwrite=False)` in `core/categorizer.py` — function logic complete, parses clean
- Settled signature: takes `category_id` (an int), not a category name — edit route already resolves name→id, schema stores `category_id`, keeps the function pure data-logic. Updated CLAUDE.md to match (it previously said `category`)
- Validation now raises `ValueError` directly (removed an earlier `try/except` that caught its own raise and returned `None` — that had reintroduced the sentinel-return design dropped on 06-12)
- Dropped the leftover `category_id is not None` branches — `category_id` is required now, never None
- Built the four-exit branch structure: no rule → INSERT, return passed id; rule with same id → return it; rule with different id + overwrite False → return existing id (conflict signal); different + overwrite True → UPDATE rule, return passed id
- Fixed table/column names against schema: `categorization_rules` table, `description_pattern` column
- Known issues for next session: (1) wire the function into `GET/POST /transactions/edit/<id>` — POST branch must first fetch the transaction's `description`; (2) latent bug at `transactions.py:154` — `fetchone()[0]` throws if category name not found, before the `if not new_category_id` guard can run; (3) top comment block in categorizer.py is now a one-liner stub, function name typo (`check_category_selection`)
- Next: wire into edit route, then CRUD UI for managing rules, then import-time batch lookup

## 2026-06-12 (end of session)
- Fixed bugs in `/categories/new` POST handler: missing parentheses on `.upper()`, missing empty-name validation (added flash + redirect back to `/categories/new`; fixed redirect target along the way — initially pointed at a nonexistent variable, then a template name, then a relative URL)
- Removed dangling `/categories/rule_check` route decorator from `routes/categories.py` — rules engine belongs in `core/categorizer.py` per 06-10 design (plain function, no HTTP layer; avoids route modules importing each other)
- Created `core/categorizer.py` with commented pseudocode skeleton for `category_rule_check(db, description, category=None, overwrite=False)` (renamed from `check_rules`)
- Design decisions amending the 06-10 rules engine design:
  - Function receives an open db connection from the caller; it never opens/closes one and never commits — caller commits, so rule write and transaction update share one transaction (also avoids SQLite write-lock contention between two connections in one request)
  - Invalid input raises `ValueError` (message names the bad argument) instead of returning sentinel codes like 0/1 — return value is always a real `category_id`, never collides with data
  - **Lookup mode (`category=None`) dropped (YAGNI)** — import pipeline will instead load all rules into a dict once per import (`description_pattern → category_id`) and match in memory; one query total instead of one per transaction. `category_rule_check` now serves only the assignment paths (transaction edit, bulk assign), so `category` becomes a required parameter
  - Conflict signal unchanged: on a rule mismatch with `overwrite=False`, return the existing rule's category_id; the route compares it against what it sent
- Known issue: `delete_category` route still missing session auth guard
- Next: rewrite skeleton to the four-exit branch structure (no rule → insert; same category → no-op; different + overwrite False → return existing; different + overwrite True → update), then implement and wire into transaction edit route

## 2026-06-10 (end of session)
- Designed auto-categorization rules engine — decisions:
  - Match on full description exact match (not LIKE/partial) — simpler, no false positives; merchant_name not reliable for CSV/OFX imports
  - `check_rules(db, description, category_id=None, overwrite=False)` function in `core/categorizer.py`
  - Behavior: no category_id → lookup only, return matching rule's category_id or None; category_id provided → create rule if none exists; if rule exists with same category do nothing; if rule exists with different category and overwrite=False return existing category_id (conflict signal); overwrite=True → update rule
  - Conflict resolution stays in the route (flash/redirect), not in the function — function handles data logic only
  - Function will be called from: single-transaction edit route (with conflict prompt), import pipeline (lookup only), bulk assign (optional, later)
- Next: implement `check_rules` in `core/categorizer.py`, then wire into edit transaction route

## 2026-06-08 (end of session)
- Added "Uncategorized" filter option to category column on transactions page — uses sentinel value `__uncategorized__` which maps to `t.category_id IS NULL` in the WHERE clause
- Added Categories nav link to layout.html
- Enforced uppercase on category names at save time — `.upper()` applied in both `/categories/new` and `/categories/edit/<id>` POST handlers
- Next: auto-categorization rules engine

## 2026-06-07 (end of session)
- Built bulk category assignment — assign a category to all currently-filtered transactions in one action
  - Added category select + "Categorize Filtered" button to `transactions.html` filter area
  - Confirm step shown inline using `{% if categorize_category %}` — displays "Assign X to N transactions?" with Confirm/Cancel
  - Confirm button uses HTML5 `formmethod="POST"` and `formaction="/transactions/bulk_categorize?{{ request.query_string.decode() }}"` to POST while preserving all filter params in the query string
  - Added `POST /transactions/bulk_categorize` route — reads filter params from `request.args`, rebuilds WHERE clause using subqueries (avoids JOIN limitation in UPDATE), updates `category_id` for all matching transactions
- Added bank category and suggested category read-only fields to `transactions_form.html`
- Fixed `transaction['account']` → `transaction['account_name']` in transactions_form.html
- Next: auto-categorization rules engine

## 2026-06-06 (end of session)
- Built `GET/POST /transactions/edit/<id>` route in `routes/transactions.py`
  - GET: fetches transaction by id with full JOIN query, fetches categories list, renders `transactions_form.html`
  - POST: looks up category id by name, guards against missing category, UPDATE category_id, commit, close, redirect
- Built `transactions_form.html` — read-only fields for id, account, date, amount, description, merchant; category dropdown with pre-selected current category and conditional parent display; blank "Select Category" option for unassigned transactions
- Added Edit button to transactions list — links to `/transactions/edit/{{ t['id'] }}`; added `t.id` to SELECT in transactions route
- Fixed category name mismatch between template variable and route (`categories` vs `categories_list`)
- Known issue: duplicate category name check not yet implemented — SQLite UNIQUE constraint will throw unhandled IntegrityError
- Next: add suggested category and bank category display to transaction edit form, then bulk category assignment

## 2026-06-04 (end of session — continued)
- Added category dropdown filter to transactions page — replaces text input; submits category name so existing `c1.name LIKE ?` route filter works unchanged
- Fixed amount filter inputs — replaced broken `filter_amount` reference with proper `amount_min`/`amount_max` stacked inputs using `placeholder` attribute for ghost text
- Fixed `<<div` typo in transactions template
- Discussed manual category assignment approach — agreed on: (1) transaction edit form for one-offs, (2) bulk assign to filtered set for large batches
- Next: build transaction edit form (category field only for now)

## 2026-06-04 (end of session)
- Built `GET/POST /categories/new` route — GET renders `category_form.html` in add mode; POST inserts new category, closes connection, redirects to `/categories`
- Built `GET/POST /categories/edit/<id>` route — GET fetches category and categories list, renders form in edit mode with pre-filled fields; POST validates name, UPDATE, close, redirect
- Built `POST /categories/delete/<id>` route — verifies category exists, DELETE, redirect
- Replaced inline add form on `categories.html` with plain `<a>` link to `/categories/new`
- Fixed several bugs: missing `household_conn.close()` on successful POST paths, `session[household_db_path]` missing quotes, wrong form field names, SQL comma before WHERE, typo in redirect URL, duplicate `class` attribute on delete form
- Fixed `category_form.html` button spacing — wrapped submit/cancel in `<div class="mt-3">`, delete form uses `class="mt-3"`
- Known issue: `confirm_id` still read in `GET /categories` route but confirm delete logic removed — dead code to clean up
- Known issue: `import os` and `REGISTRY_PATH` unused in `categories.py`
- Next: manual category assignment on transactions page

## 2026-06-03 (end of session)
- Reworked categories delete flow — abandoned inline confirm approach (button shifting layout issue on variable screen sizes); moved to account_form pattern instead
- Built `category_form.html` — single template handles add and edit; Category Name text input, Parent dropdown populated from `categories_list` with `selected` pre-fill in edit mode, Update/Create submit button, Cancel link, Delete form below (edit mode only)
- Simplified `categories.html` — removed all confirm delete logic, clean loop with Edit button per row; Delete button removed from list (delete now handled from edit form)
- Known issue: edit and delete routes in `categories.py` not yet built — next session
- Next: `GET/POST /categories/<id>/edit` and update delete route URL to `/categories/delete/<id>`

## 2026-06-02 (end of session — continued)
- Built `POST /categories/<id>/delete` route — auth guard, fetches household DB from session, DELETE by id, commit, flash, redirect to `/categories`
- Fixed several bugs in delete route: missing `category_id` parameter on function def, `session.form.get` → `session['household_db_path']`, `FROM categories DELETE` → `DELETE FROM categories WHERE id = ?`, single-value tuple missing trailing comma
- Delete working end to end
- Known issue: no confirmation before delete — to add next session (modal or confirm page)
- Next: delete confirmation, then inline edit on categories table

## 2026-06-02 (end of session)
- Fixed `account_form.html` button layout — removed `style="display:inline"` from delete form, added `class="mt-3"` to separate Delete from Update/Create; added Cancel `<a>` tag with `class="btn btn-secondary ms-2"` inside main form
- Created `routes/categories.py` Blueprint (`categories_bp`) registered in `app.py`
- Built `populate_default_categories(household_db_path)` — checks if categories table is empty, seeds 27 default categories on first run; called from `/household/new` in `app.py` immediately after `init_db()`
- Built `GET /categories` route — self-join query on categories table to fetch each category's parent name; uses table aliases `cat` and `parent` with `LEFT JOIN` so categories without parents still appear
- Built `POST /categories/new` route — inserts category name and optional parent_id; converts empty string to `None` for nullable FK
- Built `categories.html` — inline add form using `d-flex gap-2` with text input (placeholder "New Category Name"), parent dropdown, and Add Category button; table below showing Name, Parent, Edit/Delete per row
- Next: inline edit on categories table, delete route, then manual category assignment on transactions page

## 2026-06-01 (end of session — continued)
- Built accounts list page — `GET /accounts` queries household DB, passes accounts to template, Bootstrap table with Edit buttons
- Built combined new/edit form (`account_form.html`) replacing `add_account.html` — single template handles both create and edit; conditionally shows "Edit Account" vs "Add Account" heading, pre-populates fields, shows Delete button only in edit mode
- Built `GET/POST /accounts/edit/<id>` route — fetches account by id, pre-populates form, UPDATE on POST
- Built `POST /accounts/delete/<id>` route — verifies account exists, DELETE, redirect to `/accounts`
- Delete button is an inline form POSTing directly to delete route (no confirmation yet — to revisit with modal decision)
- Known issue: Edit and Delete buttons styling needs improvement — to fix next session
- Next: button styling cleanup, then move to categories management

## 2026-06-01 (end of session)
- Completed `transactions.html` rewrite — per-column filter inputs in second `<thead>` row, all aligned with column headers automatically via table layout
- Sort radio buttons (8 columns) and Order radio buttons (ASC/DESC) with sticky `checked` attributes
- Filter inputs sticky via `value="{{ variable }}"` on all inputs
- Amount column: stacked Min/Max number inputs; Date column: stacked date_from/date_to date pickers
- Added record count and total amount summary display
- `transactions.html` and sort/filter now fully working
- Discussed HTTPS/dev server security — confirmed localhost dev server is safe for personal use; HTTPS via nginx + Let's Encrypt is a deployment concern for post-CS50
- Next: categorization — categories management CRUD, manual category assignment on transactions page

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
