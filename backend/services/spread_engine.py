import os
import re
import uuid
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from PIL import Image, ImageOps
from services.color_ai import extract_ai_color_palette

class PhotoItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    relative_url: str
    original_filename: str
    event_name: str
    width: int = 1920
    height: int = 1080
    aspect_ratio: float = 1.77
    is_landscape: bool = True

class SpreadPhotoPlacement(BaseModel):
    photo_id: str
    file_path: str
    role: str
    x: int
    y: int
    width: int
    height: int
    border_width: int = 32
    border_color: Tuple[int, int, int] = (255, 255, 255)
    outer_border_width: int = 0
    outer_border_color: Optional[Tuple[int, int, int]] = None
    has_shadow: bool = True
    blend_feather: Optional[str] = None

class SpreadDesign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    spread_number: int
    event_folder_name: str
    event_display_name: str
    layout_type: str = "hero_panoramic_right"
    
    # Typography controls
    has_header_text: bool = True
    has_spine_crest: bool = True
    
    dynamic_palette: Dict[str, Any] = Field(default_factory=dict)
    
    main_title_script: str = "...Together"
    main_title_serif: str = "FOREVER"
    subtitle: str = "Two souls, one heart, countless memories.\nThis is our eternal beginning."
    
    center_label_1: str = "OUR"
    center_label_2: str = "BEAUTIFUL"
    center_label_3: str = "BEGINNING"
    color_correction_level: str = "medium"
    custom_prompt: Optional[str] = None
    
    photos: List[SpreadPhotoPlacement] = []
    preview_url: Optional[str] = None
    high_res_url: Optional[str] = None

DYNAMIC_POETRY_POOL = {
    "wedding": [
        {
            "title_script": "...Together",
            "title_serif": "FOREVER",
            "subtitle": "Two souls, one heart, countless memories.\nThis is our eternal beginning.",
            "center_1": "OUR", "center_2": "BEAUTIFUL", "center_3": "BEGINNING"
        },
        {
            "title_script": "Sacred",
            "title_serif": "VOWS & DEVOTION",
            "subtitle": "Seven sacred steps around the holy fire,\nbound by eternal prayers and timeless grace.",
            "center_1": "SACRED", "center_2": "SEVEN", "center_3": "VOWS"
        },
        {
            "title_script": "A Thousand",
            "title_serif": "YEARS OF GRACE",
            "subtitle": "From this auspicious day forward,\nyour laughter is my eternal sanctuary.",
            "center_1": "TIMELESS", "center_2": "ROYAL", "center_3": "GRACE"
        },
        {
            "title_script": "Tied in",
            "title_serif": "HOLY MATRIMONY",
            "subtitle": "Garlands exchanged under starry blessings,\nbeginning a lifelong journey made for two.",
            "center_1": "BLESSED", "center_2": "FOR", "center_3": "LIFE"
        },
        {
            "title_script": "The Promise of",
            "title_serif": "FOREVERMORE",
            "subtitle": "In your eyes, I found my home;\nin your heart, my eternal peace.",
            "center_1": "PURE", "center_2": "ETERNAL", "center_3": "LOVE"
        }
    ],
    "haldi": [
        {
            "title_script": "Sun-Kissed",
            "title_serif": "JOY & BLESSINGS",
            "subtitle": "Drenched in laughter, yellow hues,\nand the warm blessings of our loved ones.",
            "center_1": "SACRED", "center_2": "TURMERIC", "center_3": "BLESSINGS"
        },
        {
            "title_script": "Shades of",
            "title_serif": "YELLOW & SMILES",
            "subtitle": "Turmeric splattered with mischievous love,\nsurrounded by the joyful warmth of family.",
            "center_1": "HALDI", "center_2": "SPLASH", "center_3": "SMILES"
        },
        {
            "title_script": "Golden Glow of",
            "title_serif": "AUSPICIOUS JOY",
            "subtitle": "Yellow marigolds and turmeric blessings\npaving the auspicious path to tomorrow.",
            "center_1": "GOLDEN", "center_2": "HALDI", "center_3": "RITUAL"
        }
    ],
    "mehendi": [
        {
            "title_script": "Stories in",
            "title_serif": "HENNA",
            "subtitle": "Intricate vines woven with silent prayers,\ndark stains reflecting everlasting devotion.",
            "center_1": "RANG", "center_2": "AUR", "center_3": "SHAGUN"
        },
        {
            "title_script": "Tangled in",
            "title_serif": "SWEET LOVE",
            "subtitle": "His name hidden delicately in henna swirls,\na sacred promise held close to heart.",
            "center_1": "MEHENDI", "center_2": "RANG", "center_3": "BAHAR"
        }
    ],
    "sangeet": [
        {
            "title_script": "Rhythm of",
            "title_serif": "TWO HEARTS",
            "subtitle": "A sparkling night of celebration,\njoyous beats, and endless dance.",
            "center_1": "MUSIC", "center_2": "DANCE", "center_3": "LOVE"
        },
        {
            "title_script": "Sparkle &",
            "title_serif": "MIDNIGHT CHEERS",
            "subtitle": "Twirling under starry chandeliers,\nour hearts beating in perfect harmony.",
            "center_1": "NIGHT", "center_2": "FULL OF", "center_3": "STARS"
        }
    ],
    "reception": [
        {
            "title_script": "An Evening of",
            "title_serif": "ELEGANCE",
            "subtitle": "A grand celebration of timeless romance,\ngratitude, and everlasting vows.",
            "center_1": "ROYAL", "center_2": "GRAND", "center_3": "FINALE"
        },
        {
            "title_script": "Happily",
            "title_serif": "EVER AFTER",
            "subtitle": "To love, laughter, and a sparkling journey\nmade for two, blessed by all who cherish us.",
            "center_1": "CHEERS", "center_2": "TO OUR", "center_3": "FUTURE"
        },
        {
            "title_script": "Toast to the",
            "title_serif": "NEW BEGINNING",
            "subtitle": "Surrounded by loved ones and sparkling lights,\nstepping hand-in-hand into forever.",
            "center_1": "ROYAL", "center_2": "CHEERS", "center_3": "TO LOVE"
        }
    ]
}

def clean_event_name(folder_name: str) -> str:
    cleaned = re.sub(r'^[0-9]+[\s_-]*', '', folder_name).strip()
    return cleaned.title() if cleaned else folder_name.title()

def get_event_key(cleaned_name: str) -> str:
    lower = cleaned_name.lower()
    for k in DYNAMIC_POETRY_POOL.keys():
        if k in lower:
            return k
    return "wedding"

class SpreadEngine:
    def inspect_photo(self, photo_path: str) -> Tuple[int, int, float, bool]:
        try:
            with Image.open(photo_path) as im:
                im = ImageOps.exif_transpose(im)
                w, h = im.size
                aspect = w / max(1, h)
                return w, h, aspect, (aspect >= 1.15)
        except Exception:
            return 1920, 1080, 1.77, True

    def _determine_optimal_layout(
        self,
        batch: List[PhotoItem],
        last_layout: Optional[str] = None
    ) -> Tuple[str, List[PhotoItem]]:
        """
        AI Orientation & Content Solver:
        Dynamically analyzes the aspect ratios and orientations of the photos
        to select the ideal layout archetype rather than using a hardcoded template.
        """
        n = len(batch)
        landscapes = [p for p in batch if p.is_landscape]
        portraits = [p for p in batch if not p.is_landscape]
        
        if n == 2:
            return "modern_duet_fine_art", batch
            
        if n == 3:
            # If 1 portrait + 2 landscapes -> royal_storyteller_triptych (Portrait on Left, 2 Landscapes on Right)
            if len(portraits) >= 1 and len(landscapes) >= 2:
                ordered = [portraits[0], landscapes[0], landscapes[1]]
                return "royal_storyteller_triptych", ordered
            # If 1 landscape + 2 portraits -> panoramic_center_split or hero_panoramic
            elif len(landscapes) >= 1 and len(portraits) >= 2:
                if last_layout != "panoramic_center_split":
                    ordered = [landscapes[0], portraits[0], portraits[1]]
                    return "panoramic_center_split", ordered
                else:
                    ordered = [landscapes[0], portraits[0], portraits[1]]
                    return "hero_panoramic_right", ordered
            else:
                return "royal_storyteller_triptych", batch
                
        # n == 4
        # If we have landscape photos, feature them as the hero backdrop
        if landscapes:
            hero = landscapes[0]
            remaining = [p for p in batch if p.id != hero.id]
            ordered = [hero] + remaining
            
            # Alternate between right hero and left hero to keep layout fresh
            if last_layout == "hero_panoramic_right":
                return "hero_panoramic_left", ordered
            elif last_layout == "hero_panoramic_left":
                return "panoramic_center_split", ordered[:3]
            else:
                return "hero_panoramic_right", ordered
        else:
            # All portraits
            if last_layout != "royal_storyteller_triptych":
                return "royal_storyteller_triptych", batch[:3]
            else:
                return "hero_panoramic_right", batch

    def parse_prompt(self, prompt: Optional[str]) -> Tuple[Optional[int], Optional[int], str]:
        """
        Parses natural language user prompts for layout instructions:
        e.g. '10 sheets, 3 images per sheet, warm vibrant color pop'
        """
        if not prompt or not prompt.strip():
            return None, None, "medium"
            
        text = prompt.lower()
        
        # 1. Images per sheet
        img_match = re.search(r'(\d+)\s*(?:images|photos|pics|pictures)\s*(?:per\s*(?:sheet|spread|page))?', text)
        images_per_sheet = int(img_match.group(1)) if img_match else None
        if images_per_sheet and images_per_sheet not in [2, 3, 4]:
            images_per_sheet = min(max(2, images_per_sheet), 4)
            
        # 2. Number of sheets
        sheet_match = re.search(r'(\d+)\s*(?:sheets|spreads|pages)', text)
        num_sheets = int(sheet_match.group(1)) if sheet_match else None
        
        # 3. Color correction level
        if any(w in text for w in ["vibrant", "pop", "warm", "high contrast", "rich"]):
            color_level = "vibrant"
        elif any(w in text for w in ["subtle", "natural", "minimal", "soft"]):
            color_level = "subtle"
        elif any(w in text for w in ["no color", "original", "raw", "none", "untouched", "no correction"]):
            color_level = "none"
        else:
            color_level = "medium"
            
        return images_per_sheet, num_sheets, color_level

    def create_spreads_from_events(
        self,
        event_photos_map: Dict[str, List[PhotoItem]],
        theme_id: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        images_per_sheet: Optional[int] = None,
        num_sheets: Optional[int] = None,
        color_correction_level: Optional[str] = "medium"
    ) -> List[SpreadDesign]:
        """
        AI Layout Engine with User Prompt Overrides:
        - If prompt is provided, parses images_per_sheet, sheet count, color level, and style.
        - If empty or None, continues with exact default autonomous AI behavior.
        """
        # Parse natural language prompt if provided
        p_imgs, p_sheets, p_color = self.parse_prompt(custom_prompt)
        images_per_sheet = images_per_sheet or p_imgs
        num_sheets = num_sheets or p_sheets
        if custom_prompt and custom_prompt.strip():
            color_correction_level = p_color
            
        spreads: List[SpreadDesign] = []
        spread_idx = 1
        used_poem_indices: Dict[str, int] = {}
        last_layout_used: Optional[str] = None
        
        for folder_name, photos in event_photos_map.items():
            if not photos:
                continue
                
            display_name = clean_event_name(folder_name)
            event_key = get_event_key(display_name)
            poem_pool = DYNAMIC_POETRY_POOL.get(event_key, DYNAMIC_POETRY_POOL["wedding"])
            
            for p in photos:
                w, h, asp, is_land = self.inspect_photo(p.file_path)
                p.width, p.height, p.aspect_ratio, p.is_landscape = w, h, asp, is_land
                
            photo_cursor = 0
            total_photos = len(photos)
            
            while photo_cursor < total_photos:
                if num_sheets and len(spreads) >= num_sheets:
                    break
                    
                remaining_photos = total_photos - photo_cursor
                
                # Check if user specified images_per_sheet
                if images_per_sheet and images_per_sheet in [2, 3, 4]:
                    batch_size = min(images_per_sheet, remaining_photos)
                else:
                    # Default autonomous batch sizing (2, 3, or 4 based on remainder)
                    if remaining_photos == 2:
                        batch_size = 2
                    elif remaining_photos == 3:
                        batch_size = 3
                    elif remaining_photos >= 4:
                        batch_size = 4 if remaining_photos != 5 else 3 # Avoid trailing 1-photo spread
                    else:
                        batch_size = remaining_photos
                    
                raw_batch = photos[photo_cursor:photo_cursor + batch_size]
                photo_cursor += batch_size
                
                # Dynamic AI Layout Solver based on photo orientation
                layout_choice, ordered_batch = self._determine_optimal_layout(
                    raw_batch,
                    last_layout=last_layout_used
                )
                last_layout_used = layout_choice
                
                # Spread Pacing: Even spreads are clean photo spreads (no text clutter)
                is_text_spread = (spread_idx % 2 != 0)
                
                current_poem_idx = used_poem_indices.get(event_key, 0)
                selected_poem = dict(poem_pool[current_poem_idx % len(poem_pool)])
                if is_text_spread:
                    used_poem_indices[event_key] = current_poem_idx + 1
                    
                # If custom prompt is provided, tailor the subtitle or title
                if custom_prompt and custom_prompt.strip():
                    selected_poem["subtitle"] = custom_prompt.strip()
                    
                ai_palette = extract_ai_color_palette(ordered_batch[0].file_path)
                
                spread = self._build_dynamic_spread(
                    spread_num=spread_idx,
                    folder_name=folder_name,
                    display_name=display_name,
                    photos=ordered_batch,
                    layout_type=layout_choice,
                    template_info=selected_poem,
                    ai_palette=ai_palette,
                    has_header_text=is_text_spread,
                    color_correction_level=color_correction_level or "medium",
                    custom_prompt=custom_prompt
                )
                spreads.append(spread)
                spread_idx += 1
                
        return spreads

    def _build_dynamic_spread(
        self,
        spread_num: int,
        folder_name: str,
        display_name: str,
        photos: List[PhotoItem],
        layout_type: str,
        template_info: Dict[str, str],
        ai_palette: Dict[str, Any],
        has_header_text: bool = True,
        color_correction_level: str = "medium",
        custom_prompt: Optional[str] = None
    ) -> SpreadDesign:
        
        spread = SpreadDesign(
            spread_number=spread_num,
            event_folder_name=folder_name,
            event_display_name=display_name,
            layout_type=layout_type,
            has_header_text=has_header_text,
            has_spine_crest=has_header_text,
            dynamic_palette=ai_palette,
            color_correction_level=color_correction_level,
            custom_prompt=custom_prompt,
            main_title_script=template_info["title_script"],
            main_title_serif=template_info["title_serif"],
            subtitle=template_info["subtitle"],
            center_label_1=template_info.get("center_1", "OUR"),
            center_label_2=template_info.get("center_2", "BEAUTIFUL"),
            center_label_3=template_info.get("center_3", "BEGINNING"),
            photos=[]
        )
        
        n = len(photos)
        
        # -------------------------------------------------------------
        # Layout Archetype 1: hero_panoramic_right
        # -------------------------------------------------------------
        if layout_type == "hero_panoramic_right":
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[0].id, file_path=photos[0].file_path, role="background_hero_right",
                x=3200, y=0, width=7600, height=3600, border_width=0, has_shadow=False, blend_feather="soft_horizontal_left"
            ))
            card_y = 1350 if has_header_text else 850
            card_h = 1650 if has_header_text else 2150
            if n > 1:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[1].id, file_path=photos[1].file_path, role="framed_left_1",
                    x=550, y=card_y, width=1350, height=card_h, border_width=32, has_shadow=True
                ))
            if n > 2:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[2].id, file_path=photos[2].file_path, role="framed_left_2",
                    x=2050, y=card_y, width=1350, height=card_h, border_width=32, has_shadow=True
                ))
            if n > 3:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[3].id, file_path=photos[3].file_path, role="framed_right_1",
                    x=7600, y=1900, width=1800, height=1350, border_width=32, has_shadow=True
                ))

        # -------------------------------------------------------------
        # Layout Archetype 2: hero_panoramic_left
        # -------------------------------------------------------------
        elif layout_type == "hero_panoramic_left":
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[0].id, file_path=photos[0].file_path, role="background_hero_left",
                x=0, y=0, width=7600, height=3600, border_width=0, has_shadow=False, blend_feather="soft_horizontal_right"
            ))
            card_y = 1350 if has_header_text else 850
            card_h = 1650 if has_header_text else 2150
            if n > 1:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[1].id, file_path=photos[1].file_path, role="framed_right_1",
                    x=7400, y=card_y, width=1350, height=card_h, border_width=32, has_shadow=True
                ))
            if n > 2:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[2].id, file_path=photos[2].file_path, role="framed_right_2",
                    x=8900, y=card_y, width=1350, height=card_h, border_width=32, has_shadow=True
                ))
            if n > 3:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[3].id, file_path=photos[3].file_path, role="framed_left_1",
                    x=1400, y=1900, width=1800, height=1350, border_width=32, has_shadow=True
                ))

        # -------------------------------------------------------------
        # Layout Archetype 3: royal_storyteller_triptych
        # -------------------------------------------------------------
        elif layout_type == "royal_storyteller_triptych":
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[0].id, file_path=photos[0].file_path, role="feature_triptych_left",
                x=550, y=420, width=4250, height=2760, border_width=32, has_shadow=True
            ))
            if n > 1:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[1].id, file_path=photos[1].file_path, role="card_stack_top",
                    x=5800, y=420, width=4400, height=1320, border_width=30, has_shadow=True
                ))
            if n > 2:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[2].id, file_path=photos[2].file_path, role="card_stack_bot",
                    x=5800, y=1860, width=4400, height=1320, border_width=30, has_shadow=True
                ))

        # -------------------------------------------------------------
        # Layout Archetype 4: modern_duet_fine_art
        # -------------------------------------------------------------
        elif layout_type == "modern_duet_fine_art":
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[0].id, file_path=photos[0].file_path, role="duet_left",
                x=1000, y=480, width=3450, height=2650, border_width=32, has_shadow=True
            ))
            if n > 1:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[1].id, file_path=photos[1].file_path, role="duet_right",
                    x=6350, y=480, width=3450, height=2650, border_width=32, has_shadow=True
                ))

        # -------------------------------------------------------------
        # Layout Archetype 5: panoramic_center_split
        # -------------------------------------------------------------
        else:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[0].id, file_path=photos[0].file_path, role="center_panorama",
                x=2800, y=0, width=5200, height=3600, border_width=0, has_shadow=False, blend_feather="soft_horizontal_both"
            ))
            if n > 1:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[1].id, file_path=photos[1].file_path, role="flank_left",
                    x=550, y=600, width=2100, height=2400, border_width=32, has_shadow=True
                ))
            if n > 2:
                spread.photos.append(SpreadPhotoPlacement(
                    photo_id=photos[2].id, file_path=photos[2].file_path, role="flank_right",
                    x=8150, y=600, width=2100, height=2400, border_width=32, has_shadow=True
                ))

        return spread

spread_engine = SpreadEngine()
