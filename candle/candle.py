"""
Candle state management.

A candle has a lifecycle: created -> lit -> expired.
Candles burn for a configurable duration (default 24 hours)
and then fade out. Each candle can carry a dedication message.
"""

import time
import uuid


def create_candle(vigil_id, ip_address, dedication="", burn_hours=24):
    """Create a new candle in a vigil.

    Returns the candle dict.
    """
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

    for key, prefix in prefixes.items():
        if dedication.lower().startswith(key + ":"):
            name = dedication[len(key) + 1:].strip()
            return f"{prefix} {name}"

    return dedication
