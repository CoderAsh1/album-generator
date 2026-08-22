import os
import re
import uuid
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
    layout_type: str = "spacious_hero_triptych"
    
    # Typography controls
    has_header_text: bool = True       # True for opener/highlight spreads, False for clean visual spreads
    has_spine_crest: bool = True
    
    dynamic_palette: Dict[str, Any] = Field(default_factory=dict)
    
    # Dynamic AI Generated Typography (Unique per spread)
    main_title_script: str = "...Together"
    main_title_serif: str = "FOREVER"
    subtitle: str = "Two souls, one heart, countless memories.\nThis is our eternal beginning."
    
    center_label_1: str = "OUR"
    center_label_2: str = "BEAUTIFUL"
    center_label_3: str = "BEGINNING"
    
    photos: List[SpreadPhotoPlacement] = []
    preview_url: Optional[str] = None
    high_res_url: Optional[str] = None

# Comprehensive, diverse non-repeating poetry and title pool
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

    def create_spreads_from_events(
        self,
        event_photos_map: Dict[str, List[PhotoItem]],
        theme_id: Optional[str] = None
    ) -> List[SpreadDesign]:
        """
        Creates clean, spacious photobook spreads:
        - Diverse, non-repeating dynamic poetry.
        - Pacing: Alternate between Title Highlight Spreads and Clean Photo-Only Spreads (no text clutter).
        - Strictly 3 to 4 images per spread.
        """
        spreads: List[SpreadDesign] = []
        spread_idx = 1
        used_poem_indices: Dict[str, int] = {}
        
        for folder_name, photos in event_photos_map.items():
            if not photos:
                continue
                
            display_name = clean_event_name(folder_name)
            event_key = get_event_key(display_name)
            poem_pool = DYNAMIC_POETRY_POOL.get(event_key, DYNAMIC_POETRY_POOL["wedding"])
            
            for p in photos:
                w, h, asp, is_land = self.inspect_photo(p.file_path)
                p.width, p.height, p.aspect_ratio, p.is_landscape = w, h, asp, is_land
                
            chunk_size = 4
            photo_batches = [photos[i:i + chunk_size] for i in range(0, len(photos), chunk_size)]
            
            for b_idx, batch in enumerate(photo_batches):
                # Spread Pacing:
                # - Spread 1: Opener with Title & Poem
                # - Spread 2: Clean Photo Spread (NO text clutter, photos speak for themselves)
                # - Spread 3: Highlight Spread with next unique poem
                # - Spread 4: Clean Photo Spread
                is_text_spread = (b_idx % 2 == 0)
                
                # Pick unique non-repeating poem
                current_idx = used_poem_indices.get(event_key, 0)
                selected_poem = poem_pool[current_idx % len(poem_pool)]
                if is_text_spread:
                    used_poem_indices[event_key] = current_idx + 1
                    
                landscapes = [p for p in batch if p.is_landscape]
                sorted_batch = []
                if landscapes:
                    sorted_batch.append(landscapes[0])
                    remaining = [p for p in batch if p.id != landscapes[0].id]
                    sorted_batch.extend(remaining)
                else:
                    sorted_batch = batch
                    
                ai_palette = extract_ai_color_palette(sorted_batch[0].file_path)
                
                spread = self._build_spacious_spread(
                    spread_num=spread_idx,
                    folder_name=folder_name,
                    display_name=display_name,
                    photos=sorted_batch,
                    template_info=selected_poem,
                    ai_palette=ai_palette,
                    has_header_text=is_text_spread
                )
                spreads.append(spread)
                spread_idx += 1
                
        return spreads

    def _build_spacious_spread(
        self,
        spread_num: int,
        folder_name: str,
        display_name: str,
        photos: List[PhotoItem],
        template_info: Dict[str, str],
        ai_palette: Dict[str, Any],
        has_header_text: bool = True
    ) -> SpreadDesign:
        
        spread = SpreadDesign(
            spread_number=spread_num,
            event_folder_name=folder_name,
            event_display_name=display_name,
            layout_type="spacious_hero_triptych",
            has_header_text=has_header_text,
            has_spine_crest=has_header_text,
            dynamic_palette=ai_palette,
            main_title_script=template_info["title_script"],
            main_title_serif=template_info["title_serif"],
            subtitle=template_info["subtitle"],
            center_label_1=template_info["center_1"],
            center_label_2=template_info["center_2"],
            center_label_3=template_info["center_3"],
            photos=[]
        )
        
        n = len(photos)
        
        # 1. Background Hero Photo (Right ~65% of spread with soft cosine feather on left)
        hero_photo = photos[0]
        spread.photos.append(SpreadPhotoPlacement(
            photo_id=hero_photo.id,
            file_path=hero_photo.file_path,
            role="background_hero",
            x=3200,
            y=0,
            width=7600,
            height=3600,
            border_width=0,
            has_shadow=False,
            blend_feather="soft_horizontal_left"
        ))
        
        # If this is a Clean Photo-Only spread (no header text), we can position the framed cards higher and larger!
        card_y = 1350 if has_header_text else 850
        card_h = 1650 if has_header_text else 2150
        
        # 2. Left Page: Inset Portrait Card 1
        if n > 1:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[1].id,
                file_path=photos[1].file_path,
                role="framed_left_1",
                x=550,
                y=card_y,
                width=1350,
                height=card_h,
                border_width=32,
                has_shadow=True
            ))
            
        # 3. Left Page: Inset Portrait Card 2 (Side-by-side)
        if n > 2:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[2].id,
                file_path=photos[2].file_path,
                role="framed_left_2",
                x=2050,
                y=card_y,
                width=1350,
                height=card_h,
                border_width=32,
                has_shadow=True
            ))
            
        # 4. Right Page: 1 Single Elegant Accent Card (Bottom-right, strictly 4th photo)
        if n > 3:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[3].id,
                file_path=photos[3].file_path,
                role="framed_right_1",
                x=7600,
                y=1900,
                width=1800,
                height=1350,
                border_width=32,
                has_shadow=True
            ))
            
        return spread

spread_engine = SpreadEngine()
