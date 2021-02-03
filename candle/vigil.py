"""
Vigil management.

A vigil is a named collection of candles.
"""

import time
import uuid


def create_vigil(name):
    """Create a new vigil."""
    vigil = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "created_at": time.time(),
        "candle_count": 0,
    }
    return vigil
