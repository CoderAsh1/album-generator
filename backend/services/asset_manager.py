import os
import math
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import FONTS_DIR, ASSETS_DIR

logger = logging.getLogger("album_maker.assets")

def ensure_fonts():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(font_type: str, size: int):
    """
    Returns a PIL ImageFont instance using verified luxury fonts.
    """
    gv = FONTS_DIR / "great_vibes.ttf"
    
    font_preferences = {
        "script": [str(gv), "C:/Windows/Fonts/gabriola.ttf", "C:/Windows/Fonts/segoescb.ttf"],
        "title_serif": ["C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/palab.ttf"],
        "caps_serif": ["C:/Windows/Fonts/cinzel.ttf", "C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf"],
        "body_serif": ["C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/pala.ttf", "C:/Windows/Fonts/times.ttf"],
        "body_italic": ["C:/Windows/Fonts/georgiai.ttf", "C:/Windows/Fonts/palai.ttf", "C:/Windows/Fonts/timesi.ttf"],
        "sans": ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    }
    
    candidates = font_preferences.get(font_type, ["C:/Windows/Fonts/georgia.ttf"])
    for fpath in candidates:
        if Path(fpath).exists():
            try:
                return ImageFont.truetype(fpath, size)
            except Exception:
                pass
                
    return ImageFont.load_default()

def _to_rgba(color, default_alpha=200):
    if len(color) == 4:
        return color
    elif len(color) == 3:
        return (color[0], color[1], color[2], default_alpha)
    return (50, 50, 50, default_alpha)

def draw_royal_album_divider(width=1600, height=80, color=(100, 100, 100, 200)) -> Image.Image:
    """
    Draws the exact Indian album top/bottom filigree divider (matching reference image):
    Horizontal line with center scrollwork / diamond crest.
    """
    rgba = _to_rgba(color, 190)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    
    # Left and right thin lines
    draw.line([(int(width * 0.1), cy), (cx - 90, cy)], fill=rgba, width=3)
    draw.line([(cx + 90, cy), (int(width * 0.9), cy)], fill=rgba, width=3)
    
    # Center ornate scroll motif
    draw.ellipse([cx - 40, cy - 14, cx + 40, cy + 14], outline=rgba, width=3)
    draw.ellipse([cx - 18, cy - 8, cx + 18, cy + 8], outline=rgba, width=2)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=rgba)
    
    # Side scroll curls
    draw.arc([cx - 80, cy - 15, cx - 40, cy + 15], start=90, end=270, fill=rgba, width=3)
    draw.arc([cx + 40, cy - 15, cx + 80, cy + 15], start=270, end=90, fill=rgba, width=3)
    
    return img

def draw_floral_branch(size=(800, 1200), color=(49, 93, 153, 160), orientation="left") -> Image.Image:
    rgba = _to_rgba(color, 160)
    w, h = size
    scale = 2
    sw, sh = w * scale, h * scale
    img_large = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_large)
    
    points_stem = []
    steps = 60
    for i in range(steps + 1):
        t = i / steps
        if orientation == "left":
            x = sw * 0.75 - (sw * 0.5 * math.sin(t * math.pi * 0.8))
        else:
            x = sw * 0.25 + (sw * 0.5 * math.sin(t * math.pi * 0.8))
        y = sh * 0.96 - (sh * 0.9 * t)
        points_stem.append((x, y))
        
    for i in range(len(points_stem) - 1):
        prog = i / len(points_stem)
        thickness = max(3, int(14 * (1 - prog * 0.65)))
        draw.line([points_stem[i], points_stem[i+1]], fill=rgba, width=thickness)
        
    num_leaves = 14
    for i in range(1, num_leaves):
        idx = int(i * (len(points_stem) - 1) / num_leaves)
        pt = points_stem[idx]
        angle = (-45 if i % 2 == 0 else 45) + (15 if orientation == "left" else -15)
        rad = math.radians(angle)
        leaf_len = max(30, int(sw * 0.22 - (i * 5)))
        leaf_width = max(15, int(sw * 0.09 - (i * 2.5)))
        
        tip_x = pt[0] + leaf_len * math.cos(rad)
        tip_y = pt[1] - leaf_len * math.sin(rad)
        
        mid_x1 = (pt[0] + tip_x) / 2 + leaf_width * math.sin(rad)
        mid_y1 = (pt[1] + tip_y) / 2 + leaf_width * math.cos(rad)
        mid_x2 = (pt[0] + tip_x) / 2 - leaf_width * math.sin(rad)
        mid_y2 = (pt[1] + tip_y) / 2 - leaf_width * math.cos(rad)
        
        leaf_poly = [pt, (mid_x1, mid_y1), (tip_x, tip_y), (mid_x2, mid_y2)]
        fill_col = (rgba[0], rgba[1], rgba[2], max(25, int(rgba[3] * 0.25)))
        draw.polygon(leaf_poly, outline=rgba, fill=fill_col)
        draw.line([pt, (tip_x, tip_y)], fill=rgba, width=3)
        
    return img_large.resize((w, h), resample=Image.Resampling.LANCZOS)
