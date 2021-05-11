"""
Redis storage backend for Digital-Candle.

Uses Redis hashes for vigils and candles, sorted sets for
ordering, and TTL for automatic candle expiration.
"""

import json
import time
import redis


pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=50,
    decode_responses=True,
)


def get_conn():
    """Get a Redis connection from the pool."""
    return redis.Redis(connection_pool=pool)


def init_db():
    """Test the Redis connection."""
    r = get_conn()
    try:
        r.ping()
        print("Redis connection established")
    except redis.ConnectionError:
        print("ERROR: Cannot connect to Redis")
        raise


def save_vigil(vigil):
    """Save a vigil as a Redis hash."""
    r = get_conn()
    key = f"vigil:{vigil['id']}"
    r.hset(key, mapping={
        "id": vigil["id"],
        "name": vigil["name"],
        "theme": vigil.get("theme", "solidarity"),
        "dedication": vigil.get("dedication", ""),
        "created_at": str(vigil["created_at"]),
        "candle_count": str(vigil.get("candle_count", 0)),
        "peak_presence": str(vigil.get("peak_presence", 0)),
        "total_candles_lit": str(vigil.get("total_candles_lit", 0)),
    })
    r.zadd("vigils:index", {vigil["id"]: vigil["created_at"]})


def get_vigil(vigil_id):
    """Get a vigil by ID."""
    r = get_conn()
    data = r.hgetall(f"vigil:{vigil_id}")
    if not data:
        return None
    data["created_at"] = float(data["created_at"])
    data["candle_count"] = int(data["candle_count"])
    data["peak_presence"] = int(data.get("peak_presence", 0))
    data["total_candles_lit"] = int(data.get("total_candles_lit", 0))
    return data


def list_vigils():
    """List all vigils, newest first."""
    r = get_conn()
    vigil_ids = r.zrevrange("vigils:index", 0, -1)
    vigils = []
    for vid in vigil_ids:
        vigil = get_vigil(vid)
        if vigil:
            vigils.append(vigil)
    return vigils


def save_candle(candle):
    """Save a candle as a Redis hash with TTL for expiration."""
    r = get_conn()
    key = f"candle:{candle['id']}"
    r.hset(key, mapping={
        "id": candle["id"],
        "vigil_id": candle["vigil_id"],
        "lit_at": str(candle["lit_at"]),
        "expires_at": str(candle["expires_at"]),
        "dedication": candle.get("dedication", ""),
        "ip_address": candle.get("ip_address", ""),
        "active": "1" if candle.get("active", True) else "0",
    })

    # Set TTL so candle auto-expires -- no background cleanup needed
    ttl_seconds = int(candle["expires_at"] - time.time())
    if ttl_seconds > 0:
        r.expire(key, ttl_seconds)

    vigil_key = f"vigil:{candle['vigil_id']}:candles"
    r.zadd(vigil_key, {candle["id"]: candle["lit_at"]})


def get_active_candles(vigil_id):
    """Get all active candles for a vigil."""
    r = get_conn()
    vigil_key = f"vigil:{vigil_id}:candles"
    candle_ids = r.zrevrange(vigil_key, 0, -1)

    candles = []
    expired_ids = []

    for cid in candle_ids:
        key = f"candle:{cid}"
        data = r.hgetall(key)

        if not data:
            expired_ids.append(cid)
            continue

        data["lit_at"] = float(data["lit_at"])
        data["expires_at"] = float(data["expires_at"])
        data["active"] = data["active"] == "1"

        if data["active"] and data["expires_at"] > time.time():
            candles.append(data)
        else:
            expired_ids.append(cid)

    # Clean up expired references
    if expired_ids:
        r.zrem(vigil_key, *expired_ids)

    return candles


def expire_candles(vigil_id):
    """Check for and clean up expired candles. Returns expired IDs."""
    r = get_conn()
    vigil_key = f"vigil:{vigil_id}:candles"
    candle_ids = r.zrange(vigil_key, 0, -1)
    expired_ids = []
    for cid in candle_ids:
        if not r.exists(f"candle:{cid}"):
            expired_ids.append(cid)
    if expired_ids:
        r.zrem(vigil_key, *expired_ids)
    return expired_ids


def publish_event(channel, event_data):
    """Publish a SocketIO event via Redis pub/sub."""
    r = get_conn()
    r.publish(channel, json.dumps(event_data))


def subscribe_events(channel):
    """Subscribe to SocketIO events via Redis pub/sub."""
    r = get_conn()
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    return pubsub
