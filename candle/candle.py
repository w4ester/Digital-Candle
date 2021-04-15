"""
Candle state management.

A candle has a lifecycle: created -> lit -> expired.
Candles burn for a configurable duration (default 24 hours)
and then fade out.
"""

import time
import uuid


def create_candle(vigil_id, ip_address, burn_hours=24):
    """Create a new candle in a vigil."""
    candle = {
        "id": str(uuid.uuid4())[:8],
        "vigil_id": vigil_id,
        "lit_at": time.time(),
        "expires_at": time.time() + (burn_hours * 3600),
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
