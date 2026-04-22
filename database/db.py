import sqlite3
import os

# database/db.py                                                                                                                                                                         
  # Provides get_db() — the single entry point for all database connections in this app.                                                                                                   
  # Opens a SQLite connection to the given household database file, configures it, and returns it.                                                                                         
  #                                                                                                                                                                                        
  # All callers are responsible for calling conn.commit() after writes and conn.close() when done.                                                                                         
  # Foreign key enforcement is enabled on every connection via PRAGMA — required for CASCADE and                                                                                           
  # RESTRICT rules in the schema to take effect.  

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db(db_path):
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    conn = get_db(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.close()

