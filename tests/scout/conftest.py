"""Put scripts/scout on the import path for the scout unit tests."""

import pathlib
import sys

SCOUT_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "scout"
sys.path.insert(0, str(SCOUT_DIR))
