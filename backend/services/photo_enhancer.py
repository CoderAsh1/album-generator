import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

class PhotoEnhancer:
    """
    Studio-grade automated photo touch-up and enhancement pipeline:
    Supports custom color correction levels: 'none', 'subtle', 'medium', 'vibrant'.
    """
    
    def enhance_photo(self, pil_img: Image.Image, level: str = "medium") -> Image.Image:
        try:
            # 1. Ensure RGB and correct EXIF orientation
            img = ImageOps.exif_transpose(pil_img).convert("RGB")
            
            if level in ["none", "off", "0"]:
                return img
                
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # 2. Auto White Balance (Gray-World with Warm Wedding Bias)
            b, g, r = cv2.split(cv_img)
            avg_b = np.mean(b)
            avg_g = np.mean(g)
            avg_r = np.mean(r)
            avg_all = (avg_b + avg_g + avg_r) / 3.0
            
            warmth_factor = 1.04 if level == "vibrant" else (1.02 if level == "medium" else 1.01)
            scale_r = (avg_all / max(1.0, avg_r)) * warmth_factor
            scale_g = (avg_all / max(1.0, avg_g)) * 1.01
            scale_b = (avg_all / max(1.0, avg_b)) * (0.96 if level == "vibrant" else 0.98)
            
            r = np.clip(r * scale_r, 0, 255).astype(np.uint8)
            g = np.clip(g * scale_g, 0, 255).astype(np.uint8)
            b = np.clip(b * scale_b, 0, 255).astype(np.uint8)
            balanced_cv = cv2.merge([b, g, r])
            
            # 3. Shadow Recovery & Contrast in LAB Color Space (CLAHE)
            lab = cv2.cvtColor(balanced_cv, cv2.COLOR_BGR2LAB)
            l, a, b_chan = cv2.split(lab)
            
            clip_limit = 2.2 if level == "vibrant" else (1.6 if level == "medium" else 1.2)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            
            lab_enhanced = cv2.merge([l_enhanced, a, b_chan])
            rgb_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
            enhanced_pil = Image.fromarray(rgb_enhanced)
            
            # 4. Color Vibrance
            sat_boost = 1.22 if level == "vibrant" else (1.12 if level == "medium" else 1.06)
            color_enhancer = ImageEnhance.Color(enhanced_pil)
            vibrant_img = color_enhancer.enhance(sat_boost)
            
            # 5. Contrast Polish
            cont_boost = 1.08 if level == "vibrant" else (1.05 if level == "medium" else 1.02)
            contrast_enhancer = ImageEnhance.Contrast(vibrant_img)
            polished_img = contrast_enhancer.enhance(cont_boost)
            
            # 6. Micro-Sharpening (Unsharp Mask)
            sharp_percent = 145 if level == "vibrant" else (125 if level == "medium" else 100)
            sharpened = polished_img.filter(ImageFilter.UnsharpMask(radius=1.8, percent=sharp_percent, threshold=3))
            
            return sharpened
            
        except Exception:
            return pil_img

photo_enhancer = PhotoEnhancer()
