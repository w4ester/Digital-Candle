"""
Digital-Candle web server.

Flask server for digital vigil candles.
"""

import argparse
import sys
import os

from flask import Flask, render_template, request, redirect, url_for

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from candle.candle import create_candle
from candle.vigil import create_vigil
from candle.store_sqlite import (
    init_db, save_vigil, get_vigil, list_vigils,
    save_candle, get_active_candles,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "digital-candle-secret"


@app.route("/")
def index():
    """Show the main page with active vigils."""
    vigils = list_vigils()
    return render_template("index.html", vigils=vigils)


@app.route("/create", methods=["GET", "POST"])
def create():
    """Create a new vigil."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("create.html", error="Please enter a name")
        vigil = create_vigil(name)
        save_vigil(vigil)
        return redirect(url_for("vigil_page", vigil_id=vigil["id"]))
    return render_template("create.html")


@app.route("/vigil/<vigil_id>")
def vigil_page(vigil_id):
    """Show a vigil with its candles."""
    vigil = get_vigil(vigil_id)
    if not vigil:
        return redirect(url_for("index"))
    candles = get_active_candles(vigil_id)
    return render_template("index.html", vigil=vigil, candles=candles)


@app.route("/vigil/<vigil_id>/light", methods=["POST"])
def light(vigil_id):
    """Light a new candle."""
    ip = request.remote_addr or "unknown"
    candle = create_candle(vigil_id, ip)
    save_candle(candle)
    return redirect(url_for("vigil_page", vigil_id=vigil_id))


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
    app.run(host="0.0.0.0", port=args.port, debug=args.debug)
