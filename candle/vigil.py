"""
Vigil management.

A vigil is a named collection of candles. People gather around
a vigil to light candles together. Each vigil has a theme and
an optional dedication message.
"""

import time
import uuid


# Available themes for vigils
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


def create_vigil(name, theme="solidarity", dedication=""):
    """Create a new vigil.

    A vigil is where people gather to light candles together.
    """
    if theme not in THEMES:
        theme = "solidarity"

    vigil = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "theme": theme,
        "dedication": dedication,
        "created_at": time.time(),
        "candle_count": 0,
        "peak_presence": 0,
        "total_candles_lit": 0,
    }

    return vigil


def get_themes():
    """Return available vigil themes."""
    return THEMES


def update_stats(vigil, active_candles, current_presence):
    """Update vigil statistics.

    Tracks candle count, peak presence, and total candles lit.
    """
    vigil["candle_count"] = len(active_candles)
    if current_presence > vigil["peak_presence"]:
        vigil["peak_presence"] = current_presence
    return vigil


def increment_total(vigil):
    """Increment the total candles ever lit in this vigil."""
    vigil["total_candles_lit"] = vigil.get("total_candles_lit", 0) + 1
    return vigil


def format_stats(vigil):
    """Format vigil stats for display."""
    stats = {
        "name": vigil["name"],
        "theme": THEMES.get(vigil["theme"], THEMES["solidarity"])["name"],
        "candle_count": vigil["candle_count"],
        "total_candles_lit": vigil.get("total_candles_lit", 0),
        "peak_presence": vigil.get("peak_presence", 0),
        "created_at": vigil["created_at"],
    }
    return stats
