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
from candle.store_sqlite import init_db, save_candle, get_active_candles, list_vigils

app = Flask(__name__)
app.config["SECRET_KEY"] = "digital-candle-secret"


@app.route("/")
def index():
    """Show the main page."""
    candles = get_active_candles("default")
    return render_template("index.html", candles=candles)


@app.route("/light", methods=["POST"])
def light():
    """Light a new candle."""
    ip = request.remote_addr or "unknown"
    candle = create_candle("default", ip)
    save_candle(candle)
    return redirect(url_for("index"))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Digital-Candle server")
    parser.add_argument(
        "--port", type=int, default=5000,
        help="Port to run on (default: 5000)",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Run in debug mode",
    )
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
