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
    border_width: int = 30
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
    layout_type: str = "royal_indian_multiframe"
    
    dynamic_palette: Dict[str, Any] = Field(default_factory=dict)
    
    # Ribbon badge text
    ribbon_badge_text: str = "E X C E L L E N T   M O M E N T S"
    
    photos: List[SpreadPhotoPlacement] = []
    preview_url: Optional[str] = None
    high_res_url: Optional[str] = None

RIBBON_TEXT_OPTIONS = {
    "haldi": ["E X C E L L E N T   M O M E N T S", "S A C R E D   R I T U A L S", "J O Y F U L   H A L D I"],
    "wedding": ["T O G E T H E R   F O R E V E R", "R O Y A L   W E D D I N G", "E T E R N A L   V O W S"],
    "mehendi": ["B R I D A L   G L O W", "M E H E N D I   N I G H T", "C O L O R S   O F   L O V E"],
    "sangeet": ["M U S I C A L   B E A T S", "D A N C E   N I G H T", "C E L E B R A T I O N"],
    "reception": ["G R A N D   F I N A L E", "R O Y A L   R E C E P T I O N", "N E W   B E G I N N I N G"]
}

def clean_event_name(folder_name: str) -> str:
    cleaned = re.sub(r'^[0-9]+[\s_-]*', '', folder_name).strip()
    return cleaned.title() if cleaned else folder_name.title()

def get_event_key(cleaned_name: str) -> str:
    lower = cleaned_name.lower()
    for k in RIBBON_TEXT_OPTIONS.keys():
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
        Creates professional Indian Wedding Album Spreads (matching exact reference design):
        - Left: 2 Top Framed Cards + 1 Bottom Wide Card + Slate Title Ribbon.
        - Center: Large Hero Portrait with soft blend + Overlapping Colored Frame.
        - Right: 3 Stacked Candid Moments + 1 Grand Vertical Ceremony Feature + Filigree Divider Lines.
        """
        spreads: List[SpreadDesign] = []
        spread_idx = 1
        
        for folder_name, photos in event_photos_map.items():
            if not photos:
                continue
                
            display_name = clean_event_name(folder_name)
            event_key = get_event_key(display_name)
            ribbon_choices = RIBBON_TEXT_OPTIONS.get(event_key, RIBBON_TEXT_OPTIONS["wedding"])
            
            for p in photos:
                w, h, asp, is_land = self.inspect_photo(p.file_path)
                p.width, p.height, p.aspect_ratio, p.is_landscape = w, h, asp, is_land
                
            # Up to 6-8 photos per rich album spread
            batch_size = 7
            photo_batches = [photos[i:i + batch_size] for i in range(0, len(photos), batch_size)]
            
            for b_idx, batch in enumerate(photo_batches):
                badge_text = ribbon_choices[b_idx % len(ribbon_choices)]
                ai_palette = extract_ai_color_palette(batch[0].file_path)
                
                spread = self._build_royal_spread(
                    spread_num=spread_idx,
                    folder_name=folder_name,
                    display_name=display_name,
                    photos=batch,
                    badge_text=badge_text,
                    ai_palette=ai_palette
                )
                spreads.append(spread)
                spread_idx += 1
                
        return spreads

    def _build_royal_spread(
        self,
        spread_num: int,
        folder_name: str,
        display_name: str,
        photos: List[PhotoItem],
        badge_text: str,
        ai_palette: Dict[str, Any]
    ) -> SpreadDesign:
        
        spread = SpreadDesign(
            spread_number=spread_num,
            event_folder_name=folder_name,
            event_display_name=display_name,
            layout_type="royal_indian_multiframe",
            dynamic_palette=ai_palette,
            ribbon_badge_text=badge_text,
            photos=[]
        )
        
        n = len(photos)
        accent_color = ai_palette.get("accent", (210, 120, 30))
        
        # 1. Center Large Hero Photo (Close-up candid portrait with soft edge blend)
        hero_photo = photos[0]
        spread.photos.append(SpreadPhotoPlacement(
            photo_id=hero_photo.id,
            file_path=hero_photo.file_path,
            role="center_hero_portrait",
            x=3200,
            y=0,
            width=2800,
            height=3600,
            border_width=0,
            has_shadow=False,
            blend_feather="soft_horizontal_left"
        ))
        
        # 2. Left Page: Top-Left Card 1
        if n > 1:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[1].id,
                file_path=photos[1].file_path,
                role="left_top_1",
                x=180,
                y=440,
                width=1550,
                height=1050,
                border_width=30,
                has_shadow=True
            ))
            
        # 3. Left Page: Top-Right Card 2
        if n > 2:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[2].id,
                file_path=photos[2].file_path,
                role="left_top_2",
                x=1820,
                y=440,
                width=1550,
                height=1050,
                border_width=30,
                has_shadow=True
            ))
            
        # 4. Left Page: Bottom Wide Card 3
        if n > 3:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[3].id,
                file_path=photos[3].file_path,
                role="left_bottom_wide",
                x=780,
                y=1600,
                width=2050,
                height=1300,
                border_width=30,
                has_shadow=True
            ))
            
        # 5. Overlapping Floating Feature Card (Middle Right of Hero with Orange/Accent Outer Border)
        if n > 4:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[4].id,
                file_path=photos[4].file_path,
                role="center_floating_card",
                x=5400,
                y=750,
                width=1150,
                height=1900,
                border_width=24,
                outer_border_width=40,
                outer_border_color=accent_color,
                has_shadow=True
            ))
            
        # 6. Right Page: Left Column Stack (Top & Bottom)
        if n > 5:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[5].id,
                file_path=photos[5].file_path,
                role="right_stack_top",
                x=6650,
                y=380,
                width=2050,
                height=1320,
                border_width=28,
                has_shadow=True
            ))
            
        if n > 6:
            spread.photos.append(SpreadPhotoPlacement(
                photo_id=photos[6].id,
                file_path=photos[6].file_path,
                role="right_stack_bot",
                x=6650,
                y=1800,
                width=2050,
                height=1320,
                border_width=28,
                has_shadow=True
            ))
            
        # 7. Right Page: Grand Ceremony Feature Photo (Full Right Height)
        # If there's another photo or reuse
        right_hero = photos[7] if n > 7 else (photos[n-1] if n > 1 else photos[0])
        spread.photos.append(SpreadPhotoPlacement(
            photo_id=right_hero.id,
            file_path=right_hero.file_path,
            role="right_grand_feature",
            x=8850,
            y=380,
            width=1800,
            height=2740,
            border_width=30,
            has_shadow=True
        ))
        
        return spread

spread_engine = SpreadEngine()
