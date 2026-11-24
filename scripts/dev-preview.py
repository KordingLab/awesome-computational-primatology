#!/usr/bin/env python3
"""Build the site into _site/ and serve it at http://localhost:8000.

Run from anywhere:
    uv run --no-project --with pandas --with matplotlib python scripts/dev-preview.py
or, with pandas and matplotlib installed, plain `python scripts/dev-preview.py`.
Add --no-plot to skip the growth figure (it needs network for the OpenAlex panel).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-plot", action="store_true", help="skip drawing the growth figure")
    args = ap.parse_args()

    run = lambda *cmd: subprocess.run([sys.executable, *cmd], check=True, cwd=ROOT)  # noqa: E731
    run("scripts/lint_readme.py", "--strict")
    run("scripts/website_generator.py", "--out", str(SITE))
    if not args.no_plot:
        run("scripts/plot_paper_growth.py", "--out", str(SITE / "assets" / "paper_growth.png"))

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    print(f"Serving {SITE} at http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
