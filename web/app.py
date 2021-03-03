"""
Digital-Candle web server.

Flask + SocketIO server for digital vigil candles.
"""

import argparse
import sys
import os

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from candle.candle import create_candle
from candle.vigil import create_vigil, get_themes
from candle.store_sqlite import (
    init_db, save_vigil, get_vigil, list_vigils,
    save_candle, get_active_candles,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "digital-candle-secret"

socketio = SocketIO(app, async_mode="eventlet")


@app.route("/")
def index():
    """Show the main page with active vigils."""
    vigils = list_vigils()
    return render_template("index.html", vigils=vigils, themes=get_themes())


@app.route("/create", methods=["GET", "POST"])
def create():
    """Create a new vigil."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        theme = request.form.get("theme", "solidarity")
        if not name:
            return render_template("create.html", themes=get_themes(), error="Please enter a name")
        vigil = create_vigil(name, theme)
        save_vigil(vigil)
        return redirect(url_for("vigil_page", vigil_id=vigil["id"]))
    return render_template("create.html", themes=get_themes())


@app.route("/vigil/<vigil_id>")
def vigil_page(vigil_id):
    """Show a vigil with its candles."""
    vigil = get_vigil(vigil_id)
    if not vigil:
        return redirect(url_for("index"))
    candles = get_active_candles(vigil_id)
    return render_template("index.html", vigil=vigil, candles=candles, themes=get_themes())


@socketio.on("connect")
def handle_connect():
    """Handle new WebSocket connection."""
    print(f"Client connected: {request.sid}")


@socketio.on("light_candle")
def handle_light_candle(data):
    """Handle a candle lighting request via WebSocket."""
    vigil_id = data.get("vigil_id")
    if not vigil_id:
        return
    ip = request.remote_addr or "unknown"
    candle = create_candle(vigil_id, ip)
    save_candle(candle)
    emit("candle_lit", {"candle_id": candle["id"]}, broadcast=True)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Digital-Candle server")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("=" * 50)
    print("  Digital-Candle")
    print("  A place to light candles together")
    print("=" * 50)
    print(f"  Port:   {args.port}")
    print(f"  Debug:  {args.debug}")
    print("=" * 50)

    init_db()
    socketio.run(app, host="0.0.0.0", port=args.port, debug=args.debug)
