"""
Vigil management.

A vigil is a named collection of candles. People gather around
a vigil to light candles together. Each vigil has a theme.
"""

import time
import uuid


THEMES = {
    "memorial": {
        "name": "Memorial",
        "description": "Remembering someone who has passed",
        "color": "#c9a227",
    },
    "celebration": {
        "name": "Celebration",
        "description": "Celebrating a milestone or achievement",
        "color": "#e8b931",
    },
    "solidarity": {
        "name": "Solidarity",
        "description": "Standing together through difficulty",
        "color": "#d4a017",
    },
    "hope": {
        "name": "Hope",
        "description": "Looking forward to better days",
        "color": "#f0c040",
    },
}


def create_vigil(name, theme="solidarity"):
    """Create a new vigil."""
    if theme not in THEMES:
        theme = "solidarity"

    vigil = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "theme": theme,
        "created_at": time.time(),
        "candle_count": 0,
    }
    return vigil


def get_themes():
    """Return available vigil themes."""
    return THEMES
