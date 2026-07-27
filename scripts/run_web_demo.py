"""Launch the browser-friendly Open Production demo."""
from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from threading import Timer

# Allow imports from src/ without installing the package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from public_demo.server import serve_forever


def main() -> int:
    parser = argparse.ArgumentParser(description="Open Production browser demo.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind")
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the demo page in your default browser after launch.",
    )
    args = parser.parse_args()

    if args.open_browser:
        Timer(0.8, webbrowser.open, args=(f"http://{args.host}:{args.port}",)).start()

    serve_forever(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
