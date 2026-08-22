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
    layout_type: str = "spacious_hero_triptych" # Strictly 3-4 images per slide
    
    dynamic_palette: Dict[str, Any] = Field(default_factory=dict)
    
    main_title_script: str = "...Together"
    main_title_serif: str = "FOREVER"
    subtitle: str = "Two souls, one heart, countless memories.\nThis is our eternal beginning."
    
    secondary_script: str = "Memories"
    secondary_serif: str = "for a lifetime"
    secondary_quote: str = "Hand in hand, heart to heart,\nwe walk together towards a lifetime of love,\nlaughter & happiness."
    
    center_label_1: str = "OUR"
    center_label_2: str = "BEAUTIFUL"
    center_label_3: str = "BEGINNING"
    
    photos: List[SpreadPhotoPlacement] = []
    preview_url: Optional[str] = None
    high_res_url: Optional[str] = None

AI_POETRY_GENERATOR = {
    "wedding": [
        {
            "title_script": "...Together",
            "title_serif": "FOREVER",
            "subtitle": "Two souls, one heart, countless memories.\nThis is our eternal beginning.",
            "sec_script": "Memories",
            "sec_serif": "for a lifetime",
            "sec_quote": "Hand in hand, heart to heart,\nwe walk together towards a lifetime of love,\nlaughter & eternal happiness.",
            "center_1": "OUR", "center_2": "BEAUTIFUL", "center_3": "BEGINNING"
        },
        {
            "title_script": "Sacred",
            "title_serif": "VOWS & DEVOTION",
            "subtitle": "Seven sacred steps around the holy fire,\nbound by eternal prayers and timeless grace.",
            "sec_script": "Two Souls",
            "sec_serif": "United in Love",
            "sec_quote": "In every prayer, in every breath,\nI promise to love and cherish you\nthrough all lifetimes to come.",
            "center_1": "ETERNAL", "center_2": "SACRED", "center_3": "PROMISE"
        },
        {
            "title_script": "A Thousand",
            "title_serif": "YEARS OF GRACE",
            "subtitle": "From this sacred day forward,\nyour laughter is my sanctuary.",
            "sec_script": "Forever",
            "sec_serif": "Begins Today",
            "sec_quote": "Where you go, my heart follows,\nwriting the sweetest chapters\nof our shared destiny.",
            "center_1": "TIMELESS", "center_2": "ROYAL", "center_3": "GRACE"
        }
    ],
    "haldi": [
        {
            "title_script": "Sun-Kissed",
            "title_serif": "JOY & BLESSINGS",
            "subtitle": "Drenched in laughter, yellow hues,\nand the warm blessings of our loved ones.",
            "sec_script": "Golden Glow",
            "sec_serif": "of Celebration",
            "sec_quote": "Bright yellow petals and radiant smiles,\nbeginning this auspicious journey\nwith boundless joy in our hearts.",
            "center_1": "SACRED", "center_2": "TURMERIC", "center_3": "BLESSINGS"
        },
        {
            "title_script": "Shades of",
            "title_serif": "YELLOW & SMILES",
            "subtitle": "Turmeric splattered with mischievous love,\nsurrounded by the warmth of family.",
            "sec_script": "Radiant",
            "sec_serif": "Moments of Love",
            "sec_quote": "Golden memories written in laughter,\na fragrance of marigolds and sunshine,\npaving the way to tomorrow.",
            "center_1": "HALDI", "center_2": "SPLASH", "center_3": "SMILES"
        }
    ],
    "mehendi": [
        {
            "title_script": "Stories in",
            "title_serif": "HENNA",
            "subtitle": "Intricate vines woven with prayers,\ndark stains reflecting everlasting devotion.",
            "sec_script": "Melodies",
            "sec_serif": "of Joy & Grace",
            "sec_quote": "Music in the air, laughter in our hearts,\ntraditions celebrated with pure grace\nand vibrant festive colors.",
            "center_1": "RANG", "center_2": "AUR", "center_3": "SHAGUN"
        }
    ],
    "sangeet": [
        {
            "title_script": "Rhythm of",
            "title_serif": "TWO HEARTS",
            "subtitle": "A sparkling night of celebration,\njoyous beats, and endless dance.",
            "sec_script": "Dancing",
            "sec_serif": "into Forever",
            "sec_quote": "Under shimmering lights and joyful beats,\ntwo families unite with open arms,\ndancing into the sweetest forever.",
            "center_1": "MUSIC", "center_2": "DANCE", "center_3": "LOVE"
        }
    ],
    "reception": [
        {
            "title_script": "An Evening of",
            "title_serif": "ELEGANCE",
            "subtitle": "A grand celebration of timeless romance,\ngratitude, and everlasting vows.",
            "sec_script": "Happily",
            "sec_serif": "Ever After",
            "sec_quote": "To love, laughter, and a sparkling journey\nmade for two, blessed by all who cherish us.",
            "center_1": "ROYAL", "center_2": "GRAND", "center_3": "FINALE"
        }
    ]
}

def clean_event_name(folder_name: str) -> str:
    cleaned = re.sub(r'^[0-9]+[\s_-]*', '', folder_name).strip()
    return cleaned.title() if cleaned else folder_name.title()

def get_event_key(cleaned_name: str) -> str:
    lower = cleaned_name.lower()
    for k in AI_POETRY_GENERATOR.keys():
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
        Creates clean, spacious spreads strictly with 3 to 4 images per slide:
        - 1 Wide Hero Background (right side with soft feather fade)
        - 2 Framed Inset Portrait Cards (side-by-side on left page)
        - Optional 1 Right-Side Accent Card
        """
        spreads: List[SpreadDesign] = []
        spread_idx = 1
        
        for folder_name, photos in event_photos_map.items():
            if not photos:
                continue
                
            display_name = clean_event_name(folder_name)
            event_key = get_event_key(display_name)
            poem_options = AI_POETRY_GENERATOR.get(event_key, AI_POETRY_GENERATOR["wedding"])
            
            for p in photos:
                w, h, asp, is_land = self.inspect_photo(p.file_path)
                p.width, p.height, p.aspect_ratio, p.is_landscape = w, h, asp, is_land
                
            # Strictly 3 to 4 photos per spread for clean, spacious elegance
            chunk_size = 4
            photo_batches = [photos[i:i + chunk_size] for i in range(0, len(photos), chunk_size)]
            
            for b_idx, batch in enumerate(photo_batches):
                poem_idx = b_idx % len(poem_options)
                selected_poem = poem_options[poem_idx]
                
                # Landscape hero for background
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
                    ai_palette=ai_palette
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
        ai_palette: Dict[str, Any]
    ) -> SpreadDesign:
        
        spread = SpreadDesign(
            spread_number=spread_num,
            event_folder_name=folder_name,
            event_display_name=display_name,
            layout_type="spacious_hero_triptych",
            dynamic_palette=ai_palette,
            main_title_script=template_info["title_script"],
            main_title_serif=template_info["title_serif"],
            subtitle=template_info["subtitle"],
            secondary_script=template_info["sec_script"],
            secondary_serif=template_info["sec_serif"],
            secondary_quote=template_info["sec_quote"],
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
        
        # 2. Left Page: Inset Portrait Card 1
        if n > 1:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[1].id,
                file_path=photos[1].file_path,
                role="framed_left_1",
                x=550,
                y=1350,
                width=1350,
                height=1650,
                border_width=32,
                has_shadow=True
            ))
            
        # 3. Left Page: Inset Portrait Card 2 (Side-by-side with card 1)
        if n > 2:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[2].id,
                file_path=photos[2].file_path,
                role="framed_left_2",
                x=2050,
                y=1350,
                width=1350,
                height=1650,
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
