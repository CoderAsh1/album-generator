import glob
from pathlib import Path
from PIL import Image

def verify():
    jpgs = glob.glob("backend/storage/exports/*.jpg")
    print(f"Found {len(jpgs)} spread JPGs:")
    for j in jpgs:
        img = Image.open(j)
        print(f" - {Path(j).name}: Dimensions = {img.size} (Expected 10800x3600), DPI = {img.info.get('dpi')} (Expected 300x300)")
        assert img.size == (10800, 3600), f"Invalid size {img.size}"
        assert img.info.get('dpi') == (300, 300), f"Invalid dpi {img.info.get('dpi')}"

    pdfs = glob.glob("backend/storage/exports/*.pdf")
    print(f"\nFound {len(pdfs)} album PDFs:")
    for p in pdfs:
        size_mb = Path(p).stat().st_size / (1024 * 1024)
        print(f" - {Path(p).name}: Size = {size_mb:.2f} MB")

    print("\n✅ Verification Successful: All spreads strictly match 10800x3600 px @ 300 DPI!")

if __name__ == "__main__":
    verify()
