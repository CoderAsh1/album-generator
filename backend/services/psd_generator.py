import os
import io
import uuid
import zipfile
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import pytoshop
from pytoshop import enums
from pytoshop.user import nested_layers as nl

from config import SPREAD_WIDTH, SPREAD_HEIGHT, DPI, EXPORTS_DIR, THEMES
from services.spread_engine import SpreadDesign, SpreadPhotoPlacement
from services.asset_manager import get_font, draw_floral_branch, draw_diamond_crest, draw_divider_ornament
from services.photo_enhancer import photo_enhancer
from services.renderer import apply_soft_horizontal_feather, create_framed_photo_with_shadow, calculate_region_luminance, draw_text_with_halo

def pil_to_psd_layer(pil_img: Image.Image, name: str, top: int = 0, left: int = 0, opacity: int = 255) -> nl.Image:
    """
    Converts a PIL RGBA image (cropped to bounding box) to a native Photoshop layer object.
    """
    rgba = pil_img.convert("RGBA")
    w, h = rgba.size
    arr = np.array(rgba)
    
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    a = arr[:, :, 3]
    
    channels = {
        0: r,
        1: g,
        2: b,
        -1: a
    }
    
    return nl.Image(
        name=name,
        visible=True,
        opacity=opacity,
        top=top,
        left=left,
        bottom=top + h,
        right=left + w,
        channels=channels
    )

class PsdGenerator:
    def generate_spread_psd(self, spread: SpreadDesign) -> str:
        """
        Generates a 10800x3600 @ 300 DPI layered PSD file with distinct, editable layers
        for all dynamic layout archetypes.
        """
        palette = spread.dynamic_palette or THEMES["royal_blue_gold"]
        bg_color = palette.get("bg_color", (250, 251, 253))
        gold_color = palette.get("gold", (197, 142, 49))
        frame_border = (255, 255, 255)
        shadow_opacity = (palette.get("shadow_color") or [0, 0, 0, 85])[3]
        
        layers_list = []
        
        # Layer 1: Base Canvas Background
        canvas_bg = Image.new("RGBA", (SPREAD_WIDTH, SPREAD_HEIGHT), tuple(bg_color) + (255,))
        layers_list.append(pil_to_psd_layer(canvas_bg, name="1. Canvas Background", top=0, left=0))
        
        # Layer 2: Botanical Flourish (Cropped to exact bounding box)
        botanical_left = draw_floral_branch(size=(1600, 2000), color=palette.get("filigree_color", (40, 80, 140, 160)), orientation="left")
        layers_list.append(pil_to_psd_layer(botanical_left, name="2. Botanical Filigree", top=SPREAD_HEIGHT - 2000, left=0))
        
        # Layer 3: Background Unframed Photos
        bg_placements = [p for p in spread.photos if p.border_width == 0]
        for idx, p in enumerate(bg_placements):
            if Path(p.file_path).exists():
                try:
                    src_img = Image.open(p.file_path)
                    enhanced_bg = photo_enhancer.enhance_photo(src_img)
                    fitted = ImageOps.fit(enhanced_bg, (p.width, p.height), method=Image.Resampling.LANCZOS)
                    if p.blend_feather:
                        feathered = apply_soft_horizontal_feather(fitted, feather_width=2000, direction=p.blend_feather)
                    else:
                        feathered = fitted.convert("RGBA")
                    layers_list.append(pil_to_psd_layer(feathered, name=f"3. Background Hero {idx+1} ({p.role})", top=p.y, left=p.x))
                except Exception as e:
                    print(f"PSD Error on background photo: {e}")
                    
        # Layer 4: Framed Inset Photos with Realistic Drop Shadows
        framed_placements = [p for p in spread.photos if p.border_width > 0]
        for idx, p in enumerate(framed_placements):
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
                        shadow_opacity=shadow_opacity
                    )
                    layers_list.append(pil_to_psd_layer(
                        framed_img,
                        name=f"4. Framed Photo {idx+1} ({p.role})",
                        top=p.y + off_y,
                        left=p.x + off_x
                    ))
                except Exception as e:
                    print(f"PSD Error on framed photo: {e}")
                    
        # Layer 5: Typography & Titles (If enabled for this spread)
        if spread.has_header_text:
            text_layer = Image.new("RGBA", (SPREAD_WIDTH, SPREAD_HEIGHT), (0, 0, 0, 0))
            draw_txt = ImageDraw.Draw(text_layer)
            
            if spread.layout_type == "hero_panoramic_left":
                header_center_x = 8825
            elif spread.layout_type in ["modern_duet_fine_art", "panoramic_center_split"]:
                header_center_x = 5400
            else:
                header_center_x = 1975
                
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
            
            if spread.has_spine_crest and spread.layout_type != "panoramic_center_split":
                center_x = 5400
                crest = draw_diamond_crest(size=(220, 220), color=left_accent_col)
                text_layer.paste(crest, (center_x - 110, 480), crest)
                
                font_center_caps = get_font("caps_serif", 52)
                draw_text_with_halo(draw_txt, (center_x, 800), spread.center_label_1, font_center_caps, tuple(left_title_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                draw_text_with_halo(draw_txt, (center_x, 915), spread.center_label_2, font_center_caps, tuple(left_accent_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                draw_text_with_halo(draw_txt, (center_x, 1030), spread.center_label_3, font_center_caps, tuple(left_title_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                draw_text_with_halo(draw_txt, (center_x, 1160), "♡", get_font("body_serif", 60), tuple(left_accent_col), halo_color=left_halo, halo_radius=2, anchor="mm")
                
            bbox = text_layer.getbbox()
            if bbox:
                cropped_text = text_layer.crop(bbox)
                layers_list.append(pil_to_psd_layer(cropped_text, name="5. Typography & Calligraphy", top=bbox[1], left=bbox[0]))
            
        # Compile PSD File (instant raw write)
        psd = nl.nested_layers_to_psd(
            layers_list,
            color_mode=enums.ColorMode.rgb,
            size=(SPREAD_WIDTH, SPREAD_HEIGHT),
            compression=enums.Compression.raw
        )
        
        psd_filename = f"spread_{spread.spread_number:03d}_{spread.id[:8]}.psd"
        psd_path = EXPORTS_DIR / psd_filename
        
        with open(str(psd_path), "wb") as fd:
            psd.write(fd)
            
        return str(psd_path)

    def export_all_psds_as_zip(self, spreads: List[SpreadDesign], album_title: str = "Wedding Photobook") -> Tuple[str, str]:
        zip_filename = f"wedding_album_psds_{uuid.uuid4().hex[:8]}.zip"
        zip_path = EXPORTS_DIR / zip_filename
        
        with zipfile.ZipFile(str(zip_path), "w", compression=zipfile.ZIP_DEFLATED) as zip_out:
            for spread in spreads:
                spread_psd_path = self.generate_spread_psd(spread)
                zip_out.write(spread_psd_path, arcname=f"Spread_{spread.spread_number:03d}.psd")
                
        return str(zip_path), zip_filename

psd_generator = PsdGenerator()
