import os
import uuid
from pathlib import Path
from typing import List
from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
from PIL import Image
from config import EXPORTS_DIR, SPREAD_WIDTH, SPREAD_HEIGHT, DPI

# 36 inches x 12 inches in points (72 points / inch)
ALBUM_PAGE_WIDTH = 36 * 72   # 2592 pt
ALBUM_PAGE_HEIGHT = 12 * 72  # 864 pt

class PDFGenerator:
    def create_album_pdf(self, spread_image_paths: List[str], album_title: str = "Wedding Photobook") -> str:
        """
        Compiles list of 10800x3600 300DPI spreads into a single print-ready PDF.
        """
        pdf_filename = f"wedding_album_300dpi_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = EXPORTS_DIR / pdf_filename
        
        c = canvas.Canvas(str(pdf_path), pagesize=(ALBUM_PAGE_WIDTH, ALBUM_PAGE_HEIGHT))
        c.setTitle(album_title)
        c.setAuthor("AI Wedding Album Maker")
        c.setCreator("AI Wedding Album Studio (10800x3600 @ 300 DPI)")
        
        for img_path in spread_image_paths:
            if not Path(img_path).exists():
                continue
                
            # Draw the 10800x3600 image onto the 36x12 inch canvas
            c.drawImage(
                img_path,
                0,
                0,
                width=ALBUM_PAGE_WIDTH,
                height=ALBUM_PAGE_HEIGHT,
                preserveAspectRatio=True
            )
            c.showPage()
            
            import gc
            gc.collect()
            
        c.save()
        return str(pdf_path)

pdf_generator = PDFGenerator()
