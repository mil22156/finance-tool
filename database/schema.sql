
-- Database schema for the financial management application
-- This schema defines the structure of the database, including tables for users, accounts, account members, statements, and transactions.
-- users: Stores user information, including username, email, password hash, rights, and creation timestamp.
-- accounts: Stores account information, including name, institution, account type, currency, and creation timestamp.
-- account_members: Stores the relationship between users and accounts, including the role of the user in the account and the creation timestamp.
-- statements: Stores information about account statements, including the associated account, file name, file type, date range, creation timestamp, and description.
-- transactions: Stores transaction details, including the associated account, external ID, date, amount, description, merchant name, category ID, API category, pending status, notes, deduplication hash (which is a hash of a few of the key fields to make it unique), source, import date, and associated statement ID.
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rights TEXT NOT NULL CHECK(rights IN ('admin', 'read_write', 'read_only')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    institution TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK(account_type IN ('checking', 'savings', 'credit', 'investment', 'other')),
    currency TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE account_members (
    account_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner', 'member')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, account_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    filetype TEXT NOT NULL CHECK(filetype IN ('ofx', 'csv')),
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE    
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    external_id TEXT,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    merchant_name TEXT,
    category_ID INTEGER,
    api_category TEXT,
    pending BOOLEAN NOT NULL DEFAULT 0,
    notes TEXT,
    dedup_hash TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL CHECK(source IN ('csv', 'ofx', 'api', 'manual')),
    import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    statement_id INTEGER,
    FOREIGN KEY (category_ID) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (statement_id) REFERENCES statements(id) ON DELETE CASCADE
);

CREATE INDEX idx_transactions_dedup_hash ON transactions(dedup_hash);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE categorization_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description_pattern TEXT,
    merchant_pattern TEXT,
    source_pattern TEXT,
    category_id INTEGER NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    CHECK (description_pattern IS NOT NULL OR merchant_pattern IS NOT NULL OR source_pattern IS NOT NULL)
);