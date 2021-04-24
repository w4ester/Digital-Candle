# SQLite to Redis Migration Notes

Notes from migrating Digital-Candle storage from SQLite to Redis.
Kept as a record of what went wrong and what worked.

## The Problem

SQLite locks the entire database on writes. With Flask-SocketIO handling
concurrent candle lighting, even 5 simultaneous users can trigger
"database is locked" errors.

Error looks like this:
```
sqlite3.OperationalError: database is locked
```

## What I Tried

### WAL Mode (Write-Ahead Logging)
```python
cursor.execute("PRAGMA journal_mode=WAL")
```
This allows concurrent reads while a write is happening. It helped --
fewer lock errors under moderate load. But it does not solve the
fundamental problem: only one write at a time.

Under real concurrent candle lighting (10+ people all lighting candles
at the same vigil), WAL was not enough.

### Longer Timeout
```python
conn = sqlite3.connect(path, timeout=10)
```
This makes writers wait longer before giving up. But 10 seconds is too
long for a real-time app. People click "light" and wait. If the click
takes 10 seconds to process, they click again, making the problem worse.

### Connection Per Request
Tried opening and closing connections per request instead of keeping
them open. This helped slightly but added overhead.

## Why Redis

Redis is single-threaded but insanely fast. It handles concurrent access
by queuing commands internally. No locking, no conflicts.

Key advantages for this project:
1. **No locking** -- concurrent candle lighting just works
2. **TTL expiration** -- candles expire automatically, no cleanup job
3. **Pub/sub** -- cross-process SocketIO events for scaling
4. **Sorted sets** -- efficient candle ordering by time

## Data Model in Redis

### Vigils
```
vigil:{id} -> hash {name, theme, dedication, created_at, candle_count, ...}
vigils:index -> sorted set {vigil_id: created_at}
```

### Candles
```
candle:{id} -> hash {id, vigil_id, lit_at, expires_at, ...} (with TTL!)
vigil:{vigil_id}:candles -> sorted set {candle_id: lit_at}
```

The TTL on candle hashes means expired candles disappear on their own.
No background task needed. The sorted set references get cleaned up
lazily when we read active candles.

## Migration Strategy

1. Built store_redis.py with the same function signatures as store_sqlite.py
2. Both backends work -- select via command line --store flag
3. Defaulted to redis, kept sqlite as fallback
4. No data migration needed -- vigils are temporary by nature

## Connection Pool Exhaustion

Under load, the default Redis connection pool (10 connections) ran out.
Increased to 50:
```python
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, max_connections=50)
```

## Lessons

- SQLite is great for single-process apps. Not for concurrent real-time.
- WAL mode helps but does not solve concurrent writes.
- Redis TTL is perfect for temporary data with known lifetimes.
- The store interface pattern (same functions, different backends) made
  the migration much simpler than a rewrite would have been.
- Sometimes the "simple" solution (SQLite) is the right starting point.
  You learn what you need by hitting its limits.
