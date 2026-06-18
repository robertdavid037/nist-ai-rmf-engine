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


def _fix_tools_unique(conn):
    """Recreate tools table if it has UNIQUE(name) instead of UNIQUE(name, username).

    ALTER TABLE cannot change constraints, so we rename → recreate → copy.
    This only runs when the old single-column constraint is detected.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='tools'"
    ).fetchone()
    if not row:
        return  # table doesn't exist yet; schema.sql will create it correctly
    sql = (row[0] or "").upper()
    if "UNIQUE" in sql and "USERNAME" in sql:
        return  # already has UNIQUE(name, username) — nothing to do
    # Recreate with the correct composite constraint, preserving existing data
    conn.executescript("""
        DROP TABLE IF EXISTS tools_new;
        CREATE TABLE tools_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            vendor      TEXT,
            category    TEXT,
            username    TEXT NOT NULL DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE (name, username)
        );
        INSERT OR IGNORE INTO tools_new (id, name, vendor, category, username, created_at)
            SELECT id, name, vendor, category,
                   COALESCE(username, 'demo'), created_at
            FROM tools;
        DROP TABLE tools;
        ALTER TABLE tools_new RENAME TO tools;
    """)


def _migrate(conn):
    """Add columns introduced after initial schema without breaking existing DBs."""
    a_cols = [row[1] for row in conn.execute("PRAGMA table_info(assessments)")]
    if "loi25_pct" not in a_cols:
        conn.execute("ALTER TABLE assessments ADD COLUMN loi25_pct INTEGER DEFAULT 100")

    r_cols = [row[1] for row in conn.execute("PRAGMA table_info(responses)")]
    if "status" not in r_cols:
        conn.execute("ALTER TABLE responses ADD COLUMN status TEXT DEFAULT 'open'")

    t_cols = [row[1] for row in conn.execute("PRAGMA table_info(tools)")]
    if "username" not in t_cols:
        conn.execute("ALTER TABLE tools ADD COLUMN username TEXT NOT NULL DEFAULT ''")
        # Assign pre-existing seeded data to the demo user so it's visible on login
        conn.execute("UPDATE tools SET username = 'demo' WHERE username = ''")

    _fix_tools_unique(conn)
    conn.commit()


def update_response_status(response_id, status, notes=None):
    """Persist a gap's remediation status (and optionally notes) to the DB."""
    conn = get_connection()
    if notes is not None:
        conn.execute(
            "UPDATE responses SET status = ?, notes = ? WHERE id = ?",
            (status, notes, response_id),
        )
    else:
        conn.execute(
            "UPDATE responses SET status = ? WHERE id = ?",
            (status, response_id),
        )
    conn.commit()
    conn.close()


def init_db():
    """Create tables if they don't exist yet, then seed demo data if DB is empty."""
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    _migrate(conn)
    conn.commit()

    # Auto-seed demo data on first run (handles cloud deployments with ephemeral DBs)
    tool_count = conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
    conn.close()

    if tool_count == 0:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from database.seed import seed
        seed(skip_init=True)
