import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
EXPORTS_DIR = STORAGE_DIR / "exports"
PREVIEWS_DIR = STORAGE_DIR / "previews"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

# Ensure directories exist
for p in [STORAGE_DIR, UPLOADS_DIR, EXPORTS_DIR, PREVIEWS_DIR, ASSETS_DIR, FONTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Album Print Dimensions (36 inches x 12 inches @ 300 DPI)
SPREAD_WIDTH = 10800
SPREAD_HEIGHT = 3600
DPI = 300
PAGE_WIDTH = 5400  # Single page width (18 inches @ 300 DPI)
GUTTER_CENTER_X = 5400
SAFE_MARGIN = 240  # 0.8 inches safety margin from edges

# Preview Dimensions for Fast UI Rendering
PREVIEW_WIDTH = 2700
PREVIEW_HEIGHT = 900

# KIE.ai Configuration
KIE_API_KEY = os.getenv("KIE_API_KEY", "18a16cefcf2708728d1a573b0db9d063")
KIE_BASE_URL = "https://api.kie.ai/api/v1/jobs"
KIE_IMAGE_MODEL = "gpt-image-2-image-to-image"

# Color Palettes for Album Themes
THEMES = {
    "royal_blue_gold": {
        "id": "royal_blue_gold",
        "name": "Royal Sapphire & Ivory",
        "bg_color": (248, 250, 252),  # Clean crisp ivory/soft cool white
        "text_primary": (30, 58, 102),  # Deep royal sapphire navy
        "text_secondary": (71, 85, 105), # Slate gray
        "accent": (49, 93, 153),       # Sapphire blue
        "gold": (197, 142, 49),        # Warm rich gold
        "frame_border": (255, 255, 255),
        "frame_border_width": 24,
        "shadow_color": (20, 30, 45, 90),
        "filigree_color": (49, 93, 153, 160)
    },
    "regal_burgundy_gold": {
        "id": "regal_burgundy_gold",
        "name": "Imperial Burgundy & Champagne",
        "bg_color": (253, 248, 245),
        "text_primary": (114, 25, 46),  # Deep rich crimson burgundy
        "text_secondary": (115, 80, 85),
        "accent": (148, 38, 64),
        "gold": (212, 166, 76),
        "frame_border": (255, 255, 255),
        "frame_border_width": 24,
        "shadow_color": (35, 15, 20, 95),
        "filigree_color": (148, 38, 64, 150)
    },
    "emerald_royale": {
        "id": "emerald_royale",
        "name": "Emerald Royale & Warm Gold",
        "bg_color": (247, 251, 248),
        "text_primary": (20, 60, 45),   # Deep forest emerald
        "text_secondary": (70, 90, 80),
        "accent": (34, 100, 75),
        "gold": (205, 155, 60),
        "frame_border": (255, 255, 255),
        "frame_border_width": 24,
        "shadow_color": (15, 30, 25, 90),
        "filigree_color": (34, 100, 75, 150)
    },
    "pastel_rose": {
        "id": "pastel_rose",
        "name": "Blush Rose & Soft Platinum",
        "bg_color": (254, 250, 250),
        "text_primary": (74, 52, 60),
        "text_secondary": (120, 98, 105),
        "accent": (180, 110, 130),
        "gold": (180, 140, 100),
        "frame_border": (255, 255, 255),
        "frame_border_width": 24,
        "shadow_color": (40, 30, 35, 75),
        "filigree_color": (180, 110, 130, 140)
    }
}
