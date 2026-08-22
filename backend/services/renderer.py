import os
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
from typing import Optional, Dict, Any, Tuple
from config import (
    SPREAD_WIDTH, SPREAD_HEIGHT, DPI, PREVIEW_WIDTH, PREVIEW_HEIGHT,
    THEMES, EXPORTS_DIR, PREVIEWS_DIR
)
from services.spread_engine import SpreadDesign, SpreadPhotoPlacement
from services.asset_manager import (
    get_font, draw_royal_album_divider
)

def apply_soft_horizontal_feather(img: Image.Image, feather_width: int = 1600, direction: str = "left") -> Image.Image:
    """
    Applies smooth alpha feather gradient to blend background photo into adjacent color blocks.
    """
    img = img.convert("RGBA")
    w, h = img.size
    
    mask = np.ones((h, w), dtype=np.float32) * 255.0
    f_w = min(feather_width, w)
    
    if direction == "left":
        gradient = np.linspace(0, 1, f_w)
        smooth_gradient = 0.5 * (1.0 - np.cos(np.pi * gradient)) * 255.0
        mask[:, :f_w] = smooth_gradient
    elif direction == "right":
        gradient = np.linspace(1, 0, f_w)
        smooth_gradient = 0.5 * (1.0 - np.cos(np.pi * gradient)) * 255.0
        mask[:, w - f_w:] = smooth_gradient
        
    mask_img = Image.fromarray(mask.astype(np.uint8), mode="L")
    img.putalpha(mask_img)
    return img

def create_framed_photo_with_shadow(
    photo_path: str,
    target_w: int,
    target_h: int,
    border_width: int = 30,
    border_color: Tuple[int, int, int] = (255, 255, 255),
    outer_border_width: int = 0,
    outer_border_color: Optional[Tuple[int, int, int]] = None,
    shadow_offset: Tuple[int, int] = (16, 24),
    shadow_blur: int = 35,
    shadow_opacity: int = 90
) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Renders photo with white border, optional colored outer mat border, and soft drop shadow.
    """
    try:
        raw_img = Image.open(photo_path)
    except Exception:
        raw_img = Image.new("RGB", (target_w, target_h), (230, 230, 230))
        
    raw_img = ImageOps.exif_transpose(raw_img)
    
    total_border = border_width + outer_border_width
    inner_w = max(10, target_w - total_border * 2)
    inner_h = max(10, target_h - total_border * 2)
    
    cropped = ImageOps.fit(raw_img, (inner_w, inner_h), method=Image.Resampling.LANCZOS)
    
    framed = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw_f = ImageDraw.Draw(framed)
    
    # Outer colored border if specified
    if outer_border_width > 0 and outer_border_color:
        draw_f.rectangle([0, 0, target_w, target_h], fill=outer_border_color + (255,))
        # Inner white border
        draw_f.rectangle(
            [outer_border_width, outer_border_width, target_w - outer_border_width, target_h - outer_border_width],
            fill=border_color + (255,)
        )
    else:
        draw_f.rectangle([0, 0, target_w, target_h], fill=border_color + (255,))
        
    # Paste photo
    framed.paste(cropped, (total_border, total_border))
    
    # Drop shadow
    pad = shadow_blur * 3
    shadow_w = target_w + pad * 2
    shadow_h = target_h + pad * 2
    
    shadow_img = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))
    shadow_box = Image.new("L", (target_w, target_h), shadow_opacity)
    shadow_img.paste((15, 20, 30, shadow_opacity), (pad + shadow_offset[0], pad + shadow_offset[1]), shadow_box)
    shadow_blurred = shadow_img.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    shadow_blurred.paste(framed, (pad, pad), framed)
    
    return shadow_blurred, (-pad, -pad)

class SpreadRenderer:
    def render_spread(self, spread: SpreadDesign, save_preview: bool = True) -> Tuple[str, Optional[str]]:
        """
        Renders 10800x3600 300 DPI Indian Wedding Album Spread matching the exact reference design:
        - Themed left color band
        - Center close-up hero portrait
        - Framed left & right candid moments
        - Elegant top/bottom filigree divider rules
        - Lower left slate ribbon text badge
        """
        palette = spread.dynamic_palette or {}
        accent_color = palette.get("accent", (226, 134, 46)) # Vibrant warm orange/accent
        
        # 1. Base Canvas - Dual Tone Background
        canvas = Image.new("RGBA", (SPREAD_WIDTH, SPREAD_HEIGHT), (228, 225, 222, 255)) # Right side warm gray
        draw = ImageDraw.Draw(canvas)
        
        # Left Side Base Ivory ($x=0$ to $1300$)
        draw.rectangle([0, 0, 1300, SPREAD_HEIGHT], fill=(240, 237, 233, 255))
        
        # Left-Center Warm Themed Color Band ($x=1300$ to $3600$)
        draw.rectangle([1300, 0, 3600, SPREAD_HEIGHT], fill=accent_color + (255,))
        
        # 2. Render Center Hero Background Photo
        hero_placements = [p for p in spread.photos if p.role == "center_hero_portrait"]
        for p in hero_placements:
            if Path(p.file_path).exists():
                try:
                    src_img = Image.open(p.file_path)
                    src_img = ImageOps.exif_transpose(src_img)
                    fitted = ImageOps.fit(src_img, (p.width, p.height), method=Image.Resampling.LANCZOS)
                    feathered = apply_soft_horizontal_feather(fitted, feather_width=1800, direction="left")
                    canvas.paste(feathered, (p.x, p.y), feathered)
                except Exception as e:
                    print(f"Error rendering center hero photo: {e}")
                    
        # 3. Render Inset Framed Photos
        framed_placements = [p for p in spread.photos if p.role != "center_hero_portrait"]
        for p in framed_placements:
            if Path(p.file_path).exists():
                try:
                    framed_img, (off_x, off_y) = create_framed_photo_with_shadow(
                        photo_path=p.file_path,
                        target_w=p.width,
                        target_h=p.height,
                        border_width=p.border_width,
                        border_color=p.border_color,
                        outer_border_width=p.outer_border_width,
                        outer_border_color=p.outer_border_color or accent_color,
                        shadow_offset=(18, 24),
                        shadow_blur=35,
                        shadow_opacity=85
                    )
                    canvas.paste(framed_img, (p.x + off_x, p.y + off_y), framed_img)
                except Exception as e:
                    print(f"Error rendering framed photo: {e}")
                    
        # 4. Render Ornamental Top & Bottom Dividers
        # Left Top Accent Line ($x=1100$ to $2700, y=250$)
        left_top_div = draw_royal_album_divider(width=1600, height=50, color=(60, 60, 60, 200))
        canvas.paste(left_top_div, (1100, 250), left_top_div)
        
        # Right Top Divider ($x=6700$ to $8300, y=200$)
        right_top_div = draw_royal_album_divider(width=1600, height=50, color=(120, 115, 110, 220))
        canvas.paste(right_top_div, (6700, 200), right_top_div)
        
        # Right Bottom Divider ($x=6700$ to $8300, y=3320$)
        right_bot_div = draw_royal_album_divider(width=1600, height=50, color=(120, 115, 110, 220))
        canvas.paste(right_bot_div, (6700, 3320), right_bot_div)
        
        # 5. Render Lower-Left Sleek Slate Ribbon Badge
        ribbon_layer = Image.new("RGBA", (SPREAD_WIDTH, SPREAD_HEIGHT), (0, 0, 0, 0))
        draw_r = ImageDraw.Draw(ribbon_layer)
        
        rx, ry, rw, rh = 550, 3020, 3100, 180
        # Translucent elegant slate/steel gray ribbon (as in reference)
        draw_r.rectangle([rx, ry, rx + rw, ry + rh], fill=(160, 172, 185, 215))
        
        # Draw Spaced All-Caps Serif Text
        font_badge = get_font("caps_serif", 56)
        text_badge = spread.ribbon_badge_text or "E X C E L L E N T   M O M E N T S"
        draw_r.text((rx + rw // 2, ry + rh // 2), text_badge, font=font_badge, fill=(255, 255, 255, 255), anchor="mm")
        
        canvas.paste(ribbon_layer, (0, 0), ribbon_layer)
        
        # 6. Save Full 10800x3600 Resolution (300 DPI)
        final_rgb = canvas.convert("RGB")
        high_res_filename = f"spread_{spread.spread_number:03d}_{spread.id[:8]}.jpg"
        high_res_path = EXPORTS_DIR / high_res_filename
        
        final_rgb.save(
            str(high_res_path),
            format="JPEG",
            quality=95,
            dpi=(DPI, DPI),
            subsampling=0
        )
        
        # 7. Save Web Preview
        preview_rel_url = None
        if save_preview:
            preview_filename = f"preview_spread_{spread.spread_number:03d}_{spread.id[:8]}.webp"
            preview_path = PREVIEWS_DIR / preview_filename
            
            preview_img = final_rgb.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), resample=Image.Resampling.LANCZOS)
            preview_img.save(str(preview_path), format="WEBP", quality=85)
            preview_rel_url = f"/static/previews/{preview_filename}"
            
        spread.high_res_url = f"/static/exports/{high_res_filename}"
        spread.preview_url = preview_rel_url
        
        return str(high_res_path), str(PREVIEWS_DIR / f"preview_spread_{spread.spread_number:03d}_{spread.id[:8]}.webp") if save_preview else None

spread_renderer = SpreadRenderer()
