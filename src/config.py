"""Game configuration constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
MAPS_DIR = PROJECT_ROOT / "maps"

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "jjexplore"
TARGET_FPS = 60
