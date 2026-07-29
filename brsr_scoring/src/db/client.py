import sqlite3
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "brsr.db"
SCHEMA_PATH = BASE_DIR / "src" / "db" / "schema.sql"

def get_connection():
    """Returns a connection to the SQLite database."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema from schema.sql."""
    with get_connection() as conn:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
    print("Database initialized successfully.")

def run_query(query, params=(), commit=False):
    """Utility to run a query safely."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        if commit:
            conn.commit()
            return cur.rowcount
        else:
            return cur.fetchall()

if __name__ == "__main__":
    init_db()
