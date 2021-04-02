# SQLite to Redis Migration Notes

## The Problem

SQLite locks the entire database on writes. With Flask-SocketIO handling
concurrent candle lighting, even 5 simultaneous users can trigger
"database is locked" errors.

Error:
```
sqlite3.OperationalError: database is locked
```

This is a fundamental limitation of SQLite for concurrent writes.
