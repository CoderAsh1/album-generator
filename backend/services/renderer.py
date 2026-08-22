import os
import math
import numpy as np
import gc
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance, ImageFont
from typing import Optional, Dict, Any, Tuple
from config import (
    SPREAD_WIDTH, SPREAD_HEIGHT, DPI, PREVIEW_WIDTH, PREVIEW_HEIGHT,
    THEMES, EXPORTS_DIR, PREVIEWS_DIR
)
from services.spread_engine import SpreadDesign, SpreadPhotoPlacement
from services.asset_manager import (
    get_font, draw_floral_branch, draw_diamond_crest, draw_divider_ornament
)

def apply_soft_horizontal_feather(img: Image.Image, feather_width: int = 2200, direction: str = "left") -> Image.Image:
    """
    Applies a smooth cosine alpha feather gradient to blend photos into the ivory background.
    Supports left, right, and dual (both) edge feathering.
    """
    img = img.convert("RGBA")
    w, h = img.size
    
    mask = np.ones((h, w), dtype=np.float32) * 255.0
    f_w = min(feather_width, w // 2 if direction == "both" else w)
    
    if direction == "left":
        gradient = np.linspace(0, 1, f_w)
        smooth_gradient = 0.5 * (1.0 - np.cos(np.pi * gradient)) * 255.0
        mask[:, :f_w] = smooth_gradient
    elif direction == "right":
        gradient = np.linspace(1, 0, f_w)
        smooth_gradient = 0.5 * (1.0 - np.cos(np.pi * gradient)) * 255.0
        mask[:, w - f_w:] = smooth_gradient
    elif direction == "both" or direction == "soft_horizontal_both":
        grad_l = np.linspace(0, 1, f_w)
        smooth_l = 0.5 * (1.0 - np.cos(np.pi * grad_l)) * 255.0
        mask[:, :f_w] = smooth_l
        
        grad_r = np.linspace(1, 0, f_w)
        smooth_r = 0.5 * (1.0 - np.cos(np.pi * grad_r)) * 255.0
        mask[:, w - f_w:] = smooth_r
        
    mask_img = Image.fromarray(mask.astype(np.uint8), mode="L")
    img.putalpha(mask_img)
    return img

from services.photo_enhancer import photo_enhancer

def create_framed_photo_with_shadow(
    photo_path: str,
    target_w: int,
    target_h: int,
    border_width: int = 32,
    border_color: Tuple[int, int, int] = (255, 255, 255),
    shadow_offset: Tuple[int, int] = (20, 28),
    shadow_blur: int = 40,
    shadow_opacity: int = 90,
    color_level: str = "medium"
) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Crops and renders a clean white-bordered portrait with studio-grade enhancement & realistic drop shadow.
    """
    try:
        raw_img = Image.open(photo_path)
    except Exception:
        raw_img = Image.new("RGB", (target_w, target_h), (220, 220, 220))
        
    # Apply studio-grade color balancing with user-selected level
    enhanced_img = photo_enhancer.enhance_photo(raw_img, level=color_level)
    
    inner_w = max(10, target_w - border_width * 2)
    inner_h = max(10, target_h - border_width * 2)
    
    cropped = ImageOps.fit(enhanced_img, (inner_w, inner_h), method=Image.Resampling.LANCZOS)
    
    framed = Image.new("RGBA", (target_w, target_h), border_color + (255,))
    framed.paste(cropped, (border_width, border_width))
    
    draw = ImageDraw.Draw(framed)
    draw.rectangle(
        [border_width - 1, border_width - 1, target_w - border_width + 1, target_h - border_width + 1],
        outline=(210, 210, 210, 120),
        width=2
    )
    
    pad = shadow_blur * 3
    shadow_w = target_w + pad * 2
    shadow_h = target_h + pad * 2
    
    shadow_img = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))
    shadow_box = Image.new("L", (target_w, target_h), shadow_opacity)
    
    shadow_img.paste(
        (15, 20, 30, shadow_opacity),
        (pad + shadow_offset[0], pad + shadow_offset[1]),
        shadow_box
    )
    shadow_blurred = shadow_img.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    shadow_blurred.paste(framed, (pad, pad), framed)
    
    return shadow_blurred, (-pad, -pad)

def calculate_region_luminance(canvas: Image.Image, x: int, y: int, w: int, h: int) -> float:
    box = (max(0, x), max(0, y), min(canvas.width, x + w), min(canvas.height, y + h))
    crop = canvas.crop(box).convert("RGB")
    stat = np.array(crop).mean(axis=(0, 1))
    lum = (0.299 * stat[0] + 0.587 * stat[1] + 0.114 * stat[2]) / 255.0
    return float(lum)

def draw_text_with_halo(
    draw: ImageDraw.ImageDraw,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    halo_color: Tuple[int, int, int, int] = (0, 0, 0, 160),
    halo_radius: int = 3,
    anchor: Optional[str] = None
):
    x, y = pos
    if halo_radius > 0:
        for dx in range(-halo_radius, halo_radius + 1, 2):
            for dy in range(-halo_radius, halo_radius + 1, 2):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=halo_color, anchor=anchor)
                
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

class SpreadRenderer:
    def render_spread(self, spread: SpreadDesign, save_preview: bool = True) -> Tuple[str, Optional[str]]:
        """
        Renders full 10800x3600 @ 300 DPI spread for all dynamic layout archetypes.
        """
        palette = spread.dynamic_palette or THEMES["royal_blue_gold"]
        bg_color = palette.get("bg_color", (250, 251, 253))
        gold_color = palette.get("gold", (197, 142, 49))
        frame_border = (255, 255, 255)
        shadow_opacity = (palette.get("shadow_color") or [0, 0, 0, 85])[3]
        
        # 1. Base Canvas
        canvas = Image.new("RGBA", (SPREAD_WIDTH, SPREAD_HEIGHT), tuple(bg_color) + (255,))
        
        color_level = spread.color_correction_level or "medium"
        
        # 2. Render Background Unframed Photos
        bg_placements = [p for p in spread.photos if p.border_width == 0]
        for p in bg_placements:
            if Path(p.file_path).exists():
                try:
                    src_img = Image.open(p.file_path)
                    enhanced_bg = photo_enhancer.enhance_photo(src_img, level=color_level)
                    fitted = ImageOps.fit(enhanced_bg, (p.width, p.height), method=Image.Resampling.LANCZOS)
                    if p.blend_feather:
                        feathered = apply_soft_horizontal_feather(fitted, feather_width=2000, direction=p.blend_feather)
                    else:
                        feathered = fitted.convert("RGBA")
                    canvas.paste(feathered, (p.x, p.y), feathered)
                except Exception as e:
                    print(f"Error rendering background photo: {e}")
                    
        # 3. Render Inset Framed Photos
        framed_placements = [p for p in spread.photos if p.border_width > 0]
        for p in framed_placements:
            if Path(p.file_path).exists():
                try:
                    framed_img, (off_x, off_y) = create_framed_photo_with_shadow(
                        photo_path=p.file_path,
                        target_w=p.width,
                        target_h=p.height,
                        border_width=p.border_width,
                        border_color=frame_border,
                        shadow_offset=(20, 28),
                        shadow_blur=38,
                        shadow_opacity=shadow_opacity,
                        color_level=color_level
                    )
                    canvas.paste(framed_img, (p.x + off_x, p.y + off_y), framed_img)
                except Exception as e:
                    print(f"Error rendering framed photo: {e}")
                    
        # 4. Render Botanical Floral Flourishes (Corner accents)
        botanical_left = draw_floral_branch(size=(1600, 2000), color=palette.get("filigree_color", (40, 80, 140, 160)), orientation="left")
        canvas.paste(botanical_left, (0, SPREAD_HEIGHT - 2000), botanical_left)
        
        # 5. Render Dynamic Typography
        if spread.has_header_text:
            text_layer = Image.new("RGBA", (SPREAD_WIDTH, SPREAD_HEIGHT), (0, 0, 0, 0))
            draw_txt = ImageDraw.Draw(text_layer)
            
            # Header position varies by layout archetype
            if spread.layout_type == "hero_panoramic_left":
                header_center_x = 8825  # Placed on right ivory margin
            elif spread.layout_type in ["modern_duet_fine_art", "panoramic_center_split"]:
                header_center_x = 5400  # Centered on top
            else:
                header_center_x = 1975  # Placed on left ivory margin
                
            left_zone_lum = calculate_region_luminance(canvas, header_center_x - 1200, 250, 2400, 800)
            if left_zone_lum < 0.45:
                left_title_col = (255, 255, 255)
                left_accent_col = (245, 220, 145)
                left_sec_col = (230, 235, 245)
                left_halo = (0, 0, 0, 180)
            else:
                left_title_col = palette.get("text_primary", (25, 45, 80))
                left_accent_col = palette.get("accent", (40, 80, 140))
                left_sec_col = palette.get("text_secondary", (70, 80, 95))
                left_halo = (255, 255, 255, 180)
                
            font_script_title = get_font("script", 260)
            font_serif_title = get_font("caps_serif", 105)
            font_poem = get_font("body_serif", 64)
            
            bbox_script = draw_txt.textbbox((0, 0), spread.main_title_script, font=font_script_title)
            script_w = bbox_script[2] - bbox_script[0]
            bbox_serif = draw_txt.textbbox((0, 0), spread.main_title_serif, font=font_serif_title)
            serif_w = bbox_serif[2] - bbox_serif[0]
            
            total_title_w = script_w + 35 + serif_w
            start_x = header_center_x - (total_title_w // 2)
            
            draw_text_with_halo(draw_txt, (start_x, 300), spread.main_title_script, font_script_title, tuple(left_title_col), halo_color=left_halo, halo_radius=3)
            draw_text_with_halo(draw_txt, (start_x + script_w + 35, 415), spread.main_title_serif, font_serif_title, tuple(left_accent_col), halo_color=left_halo, halo_radius=3)
            
            small_flourish = draw_floral_branch(size=(220, 220), color=left_accent_col, orientation="right")
            text_layer.paste(small_flourish, (start_x + total_title_w + 20, 340), small_flourish)
            
            lines = spread.subtitle.split("\n")
            y_text = 610
            for line in lines:
                draw_text_with_halo(draw_txt, (header_center_x, y_text), line, font_poem, tuple(left_sec_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                y_text += 82
                
            left_divider = draw_divider_ornament(width=700, height=50, color=gold_color)
            text_layer.paste(left_divider, (header_center_x - 350, y_text + 10), left_divider)
            
            # Center Spine Crest (Only when appropriate and center is not obstructed)
            if spread.has_spine_crest and spread.layout_type != "panoramic_center_split":
                center_x = 5400
                crest = draw_diamond_crest(size=(220, 220), color=left_accent_col)
                text_layer.paste(crest, (center_x - 110, 480), crest)
                
                font_center_caps = get_font("caps_serif", 52)
                draw_text_with_halo(draw_txt, (center_x, 800), spread.center_label_1, font_center_caps, tuple(left_title_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                draw_text_with_halo(draw_txt, (center_x, 915), spread.center_label_2, font_center_caps, tuple(left_accent_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                draw_text_with_halo(draw_txt, (center_x, 1030), spread.center_label_3, font_center_caps, tuple(left_title_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                draw_text_with_halo(draw_txt, (center_x, 1160), "♡", get_font("body_serif", 60), tuple(left_accent_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                
            canvas.paste(text_layer, (0, 0), text_layer)
            
            # Free text layer memory immediately
            del text_layer
            gc.collect()
            
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
        
        # Free heavy RGBA canvas immediately
        del canvas
        gc.collect()
        
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
        
        # Free final RGB and run full sweep before next spread
        del final_rgb
        gc.collect()
        
        return str(high_res_path), str(PREVIEWS_DIR / f"preview_spread_{spread.spread_number:03d}_{spread.id[:8]}.webp") if save_preview else None

spread_renderer = SpreadRenderer()
