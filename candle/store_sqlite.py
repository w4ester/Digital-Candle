"""
SQLite storage backend for Digital-Candle.

Stores vigils, candles, and presence logs in SQLite.
Works fine for single-user testing but locks under
concurrent access -- 5 simultaneous users is enough
to trigger database locked errors.

WAL mode helps but does not fully solve the problem.
See experiments/sqlite_to_redis_notes.md for the full story.
"""

import sqlite3
import time
import json


DB_PATH = "candle.db"


def init_db(db_path=None):
    """Initialize the SQLite database with required tables."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Enable WAL mode for better concurrent reads
    cursor.execute("PRAGMA journal_mode=WAL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vigils (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            theme TEXT DEFAULT 'solidarity',
            dedication TEXT DEFAULT '',
            created_at REAL,
            candle_count INTEGER DEFAULT 0,
            peak_presence INTEGER DEFAULT 0,
            total_candles_lit INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            id TEXT PRIMARY KEY,
            vigil_id TEXT NOT NULL,
            lit_at REAL,
            expires_at REAL,
            dedication TEXT DEFAULT '',
            ip_address TEXT,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (vigil_id) REFERENCES vigils(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presence_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vigil_id TEXT NOT NULL,
            session_id TEXT,
            connected_at REAL,
            disconnected_at REAL,
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

    cursor.execute("""
        INSERT OR REPLACE INTO vigils
        (id, name, theme, dedication, created_at, candle_count,
         peak_presence, total_candles_lit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vigil["id"], vigil["name"], vigil["theme"],
        vigil.get("dedication", ""), vigil["created_at"],
        vigil.get("candle_count", 0), vigil.get("peak_presence", 0),
        vigil.get("total_candles_lit", 0),
    ))

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
        (id, vigil_id, lit_at, expires_at, dedication, ip_address, active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        candle["id"], candle["vigil_id"], candle["lit_at"],
        candle["expires_at"], candle.get("dedication", ""),
        candle.get("ip_address", ""), 1 if candle.get("active", True) else 0,
    ))

    conn.commit()
    conn.close()


def get_active_candles(vigil_id, db_path=None):
    """Get all active (non-expired) candles for a vigil."""
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


def expire_candles(vigil_id, db_path=None):
    """Mark expired candles as inactive. Returns list of expired candle IDs."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    now = time.time()

    # Find candles to expire
    cursor.execute("""
        SELECT id FROM candles
        WHERE vigil_id = ? AND active = 1 AND expires_at <= ?
    """, (vigil_id, now))
    expired_ids = [row[0] for row in cursor.fetchall()]

    # Mark them inactive
    if expired_ids:
        cursor.execute("""
            UPDATE candles SET active = 0
            WHERE vigil_id = ? AND active = 1 AND expires_at <= ?
        """, (vigil_id, now))

    conn.commit()
    conn.close()

    return expired_ids


def log_presence(vigil_id, session_id, db_path=None):
    """Log a presence connection."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO presence_log (vigil_id, session_id, connected_at)
        VALUES (?, ?, ?)
    """, (vigil_id, session_id, time.time()))

    conn.commit()
    conn.close()


def log_disconnect(session_id, db_path=None):
    """Log a presence disconnection."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE presence_log SET disconnected_at = ?
        WHERE session_id = ? AND disconnected_at IS NULL
    """, (time.time(), session_id))

    conn.commit()
    conn.close()
