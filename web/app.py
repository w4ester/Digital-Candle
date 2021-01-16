"""
Digital-Candle web server.

Flask server for digital vigil candles.
"""

import argparse
from flask import Flask, render_template

app = Flask(__name__)
app.config["SECRET_KEY"] = "digital-candle-secret"


@app.route("/")
def index():
    """Show the main page."""
    return "<h1>Digital-Candle</h1><p>Coming soon.</p>"


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

    app.run(host="0.0.0.0", port=args.port, debug=args.debug)
