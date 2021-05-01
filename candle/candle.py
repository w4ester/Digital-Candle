"""
Candle state management.

A candle has a lifecycle: created -> lit -> expired.
Candles burn for a configurable duration (default 24 hours)
and then fade out. Each candle can carry a dedication message.
"""

import time
import uuid


# Rate limiting: max candles per IP per minute
RATE_LIMIT = 10
RATE_WINDOW = 60  # seconds

# Track lighting attempts by IP
# { ip_address: [timestamp, timestamp, ...] }
rate_tracker = {}


def create_candle(vigil_id, ip_address, dedication="", burn_hours=24):
    """Create a new candle in a vigil.

    Returns the candle dict or None if rate limited.
    """
    # Check rate limit
    if not check_rate_limit(ip_address):
        return None

    candle = {
        "id": str(uuid.uuid4())[:8],
        "vigil_id": vigil_id,
        "lit_at": time.time(),
        "expires_at": time.time() + (burn_hours * 3600),
        "dedication": dedication,
        "ip_address": ip_address,
        "active": True,
    }

    return candle


def check_rate_limit(ip_address):
    """Check if an IP address has exceeded the rate limit.

    Returns True if the request is allowed, False if rate limited.
    """
    now = time.time()
    window_start = now - RATE_WINDOW

    # Clean old entries
    if ip_address in rate_tracker:
        rate_tracker[ip_address] = [
            t for t in rate_tracker[ip_address] if t > window_start
        ]
    else:
        rate_tracker[ip_address] = []

    # Check limit
    if len(rate_tracker[ip_address]) >= RATE_LIMIT:
        return False

    # Record this attempt
    rate_tracker[ip_address].append(now)
    return True


def is_expired(candle):
    """Check if a candle has burned out."""
    return time.time() > candle["expires_at"]


def extinguish(candle):
    """Mark a candle as no longer active."""
    candle["active"] = False
    return candle


def time_remaining(candle):
    """Get seconds remaining before candle expires."""
    remaining = candle["expires_at"] - time.time()
    return max(0, remaining)


def format_dedication(dedication):
    """Format a dedication message for display.

    Supports prefixes: 'memory', 'honor', 'thinking'
    """
    if not dedication:
        return ""

    prefixes = {
        "memory": "In memory of",
        "honor": "In honor of",
        "thinking": "Thinking of",
    }

    # Check if dedication starts with a known prefix key
    for key, prefix in prefixes.items():
        if dedication.lower().startswith(key + ":"):
            name = dedication[len(key) + 1:].strip()
            return f"{prefix} {name}"

    return dedication
