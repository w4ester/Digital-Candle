"""
Digital-Candle web server.

Flask + SocketIO server for real-time vigil candles.
People light candles as a form of presence and solidarity.
Everyone watching a vigil sees new candles appear in real time.
"""

import argparse
import time
import sys
import os

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from candle.candle import create_candle, is_expired, format_dedication
from candle.vigil import create_vigil, get_themes, update_stats, increment_total, format_stats


app = Flask(__name__)
app.config["SECRET_KEY"] = "digital-candle-secret"

socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# Storage backend -- set by command line argument
store = None

# Track presence per vigil room
# { vigil_id: set(session_ids) }
presence = {}


def get_store(store_type):
    """Import and initialize the selected storage backend."""
    if store_type == "redis":
        from candle import store_redis
        store_redis.init_db()
        return store_redis
    else:
        from candle import store_sqlite
        store_sqlite.init_db()
        return store_sqlite


# ============================================================
# Flask Routes
# ============================================================

@app.route("/")
def index():
    """Show the main page with active vigils."""
    vigils = store.list_vigils()
    return render_template("index.html", vigils=vigils, themes=get_themes())


@app.route("/create", methods=["GET", "POST"])
def create():
    """Create a new vigil."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        theme = request.form.get("theme", "solidarity")
        dedication = request.form.get("dedication", "").strip()

        if not name:
            return render_template(
                "create.html",
                themes=get_themes(),
                error="Please enter a name for the vigil",
            )

        vigil = create_vigil(name, theme, dedication)
        store.save_vigil(vigil)
        return redirect(url_for("vigil_page", vigil_id=vigil["id"]))

    return render_template("create.html", themes=get_themes())


@app.route("/vigil/<vigil_id>")
def vigil_page(vigil_id):
    """Show a vigil with its candles."""
    vigil = store.get_vigil(vigil_id)
    if not vigil:
        return redirect(url_for("index"))

    candles = store.get_active_candles(vigil_id)
    theme = get_themes().get(vigil.get("theme", "solidarity"), get_themes()["solidarity"])
    presence_count = len(presence.get(vigil_id, set()))

    return render_template(
        "index.html",
        vigil=vigil,
        candles=candles,
        theme=theme,
        presence_count=presence_count,
        themes=get_themes(),
    )


@app.route("/api/vigil/<vigil_id>/stats")
def vigil_stats(vigil_id):
    """API endpoint for vigil statistics."""
    vigil = store.get_vigil(vigil_id)
    if not vigil:
        return jsonify({"error": "vigil not found"}), 404

    candles = store.get_active_candles(vigil_id)
    current_presence = len(presence.get(vigil_id, set()))
    update_stats(vigil, candles, current_presence)

    stats = format_stats(vigil)
    stats["active_watchers"] = current_presence
    return jsonify(stats)


# ============================================================
# SocketIO Events
# ============================================================

@socketio.on("connect")
def handle_connect():
    """Handle new WebSocket connection."""
    pass


@socketio.on("join_vigil")
def handle_join_vigil(data):
    """Handle a user joining a vigil room."""
    vigil_id = data.get("vigil_id")
    if not vigil_id:
        return

    join_room(vigil_id)

    # Track presence
    if vigil_id not in presence:
        presence[vigil_id] = set()
    presence[vigil_id].add(request.sid)

    count = len(presence[vigil_id])
    emit("presence_update", {"count": count}, room=vigil_id)


@socketio.on("leave_vigil")
def handle_leave_vigil(data):
    """Handle a user leaving a vigil room."""
    vigil_id = data.get("vigil_id")
    if not vigil_id:
        return

    leave_room(vigil_id)

    # Update presence
    if vigil_id in presence:
        presence[vigil_id].discard(request.sid)
        count = len(presence[vigil_id])
        emit("presence_update", {"count": count}, room=vigil_id)


@socketio.on("light_candle")
def handle_light_candle(data):
    """Handle a candle lighting request."""
    vigil_id = data.get("vigil_id")
    dedication = data.get("dedication", "")

    if not vigil_id:
        return

    # Get client IP for rate limiting
    ip = request.remote_addr or "unknown"

    candle = create_candle(vigil_id, ip, dedication)

    if candle is None:
        emit("rate_limited", {
            "message": "Too many candles -- please wait a moment"
        })
        return

    # Save candle
    store.save_candle(candle)

    # Update vigil stats
    vigil = store.get_vigil(vigil_id)
    if vigil:
        increment_total(vigil)
        store.save_vigil(vigil)

    # Format dedication for display
    display_dedication = format_dedication(dedication)

    # Broadcast to everyone in the vigil room
    emit("candle_lit", {
        "candle_id": candle["id"],
        "dedication": display_dedication,
        "expires_at": candle["expires_at"],
    }, room=vigil_id)


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection.

    Clean up presence tracking. Important to get this right --
    browser tab close does not always fire leave_vigil.
    """
    # Remove from all vigil presence sets
    for vigil_id in list(presence.keys()):
        if request.sid in presence[vigil_id]:
            presence[vigil_id].discard(request.sid)
            count = len(presence[vigil_id])
            # Only emit if there are still people watching
            if count >= 0:
                socketio.emit(
                    "presence_update",
                    {"count": count},
                    room=vigil_id,
                )


# ============================================================
# Startup
# ============================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Digital-Candle vigil server")
    parser.add_argument(
        "--port", type=int, default=5000,
        help="Port to run on (default: 5000)",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Run in debug mode",
    )
    parser.add_argument(
        "--store", choices=["sqlite", "redis"], default="redis",
        help="Storage backend (default: redis)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("=" * 50)
    print("  Digital-Candle")
    print("  A place to light candles together")
    print("=" * 50)
    print(f"  Store:  {args.store}")
    print(f"  Port:   {args.port}")
    print(f"  Debug:  {args.debug}")
    print("=" * 50)

    store = get_store(args.store)

    socketio.run(app, host="0.0.0.0", port=args.port, debug=args.debug)
