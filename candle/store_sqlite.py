"""
SQLite storage backend for Digital-Candle.

Stores vigils and candles in SQLite.
"""

import sqlite3
import time


DB_PATH = "candle.db"


def init_db(db_path=None):
    """Initialize the SQLite database with required tables."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vigils (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            id TEXT PRIMARY KEY,
            vigil_id TEXT NOT NULL,
            lit_at REAL,
            expires_at REAL,
            ip_address TEXT,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (vigil_id) REFERENCES vigils(id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"SQLite database initialized at {path}")


def save_vigil(vigil, db_path=None):
    """Save a vigil to the database."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO vigils (id, name, created_at) VALUES (?, ?, ?)",
        (vigil["id"], vigil["name"], vigil["created_at"]),
    )
    conn.commit()
    conn.close()


def get_vigil(vigil_id, db_path=None):
    """Get a vigil by ID."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vigils WHERE id = ?", (vigil_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def list_vigils(db_path=None):
    """List all vigils."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vigils ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_candle(candle, db_path=None):
    """Save a candle to the database."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO candles
        (id, vigil_id, lit_at, expires_at, ip_address, active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        candle["id"], candle["vigil_id"], candle["lit_at"],
        candle["expires_at"], candle.get("ip_address", ""),
        1 if candle.get("active", True) else 0,
    ))
    conn.commit()
    conn.close()


def get_active_candles(vigil_id, db_path=None):
    """Get all active candles for a vigil."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = time.time()
    cursor.execute("""
        SELECT * FROM candles
        WHERE vigil_id = ? AND active = 1 AND expires_at > ?
        ORDER BY lit_at DESC
    """, (vigil_id, now))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
