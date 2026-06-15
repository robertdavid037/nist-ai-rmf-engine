import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "assessments.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    """Return a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["column_name"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist yet, then seed demo data if DB is empty."""
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()

    # Auto-seed demo data on first run (handles cloud deployments with ephemeral DBs)
    tool_count = conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
    conn.close()

    if tool_count == 0:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from database.seed import seed
        seed(skip_init=True)
