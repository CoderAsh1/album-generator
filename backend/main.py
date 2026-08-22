import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import (
    STORAGE_DIR, UPLOADS_DIR, EXPORTS_DIR, PREVIEWS_DIR, THEMES,
    SPREAD_WIDTH, SPREAD_HEIGHT, DPI
)
from services.spread_engine import (
    spread_engine, PhotoItem, SpreadDesign, clean_event_name
)
from services.renderer import spread_renderer
from services.pdf_generator import pdf_generator
from services.kie_client import kie_client
from services.asset_manager import ensure_fonts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("album_maker.api")

app = FastAPI(
    title="AI Wedding Album Maker API",
    description="Backend for 10800x3600 @ 300 DPI Wedding Photobook Designer",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/previews", StaticFiles(directory=str(PREVIEWS_DIR)), name="previews")
app.mount("/static/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")

SESSION_STATE: Dict[str, Any] = {
    "photos_by_event": {},
    "spreads": [],
    "last_pdf_path": None,
    "last_pdf_filename": None,
}

@app.on_event("startup")
async def startup_event():
    ensure_fonts()
    logger.info("AI Wedding Album Maker API initialized.")

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "dimensions": f"{SPREAD_WIDTH}x{SPREAD_HEIGHT}",
        "dpi": DPI,
        "kie_model": "gpt-image-2-image-to-image"
    }

@app.get("/api/themes")
async def get_themes():
    return {"themes": THEMES}

@app.post("/api/upload")
async def upload_photos(
    files: List[UploadFile] = File(...),
    folder_names: Optional[List[str]] = Form(None),
    relative_paths: Optional[List[str]] = Form(None)
):
    """
    Accepts user photo uploads. Clears out all old/demo session data automatically
    so that only the user's uploaded folders and photos are in the album.
    """
    # Clear previous state on new upload
    SESSION_STATE["photos_by_event"] = {}
    SESSION_STATE["spreads"] = []
    
    uploaded_items: List[PhotoItem] = []
    
    for idx, file in enumerate(files):
        rel_path = relative_paths[idx] if (relative_paths and idx < len(relative_paths)) else file.filename
        
        parts = Path(rel_path).parts
        if len(parts) > 1:
            event_folder = parts[0]
            clean_filename = parts[-1]
        else:
            event_folder = (folder_names[idx] if folder_names and idx < len(folder_names) else "001 - Wedding")
            clean_filename = file.filename
            
        event_dir = UPLOADS_DIR / event_folder
        event_dir.mkdir(parents=True, exist_ok=True)
        
        unique_name = f"{uuid.uuid4().hex[:6]}_{clean_filename}"
        target_path = event_dir / unique_name
        
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        rel_url = f"/static/uploads/{event_folder}/{unique_name}"
        
        photo_item = PhotoItem(
            file_path=str(target_path),
            relative_url=rel_url,
            original_filename=clean_filename,
            event_name=event_folder
        )
        
        if event_folder not in SESSION_STATE["photos_by_event"]:
            SESSION_STATE["photos_by_event"][event_folder] = []
        SESSION_STATE["photos_by_event"][event_folder].append(photo_item)
        uploaded_items.append(photo_item)
        
    return {
        "message": f"Successfully uploaded {len(uploaded_items)} photos",
        "events": list(SESSION_STATE["photos_by_event"].keys()),
        "total_photos": sum(len(v) for v in SESSION_STATE["photos_by_event"].values())
    }

@app.post("/api/generate-album")
async def generate_album(theme_id: Optional[str] = None):
    """
    AI Model Decision: Analyzes uploaded photos & events, determines optimal layouts,
    applies theme & poetry, and renders 10800x3600 @ 300 DPI spreads.
    """
    if not SESSION_STATE["photos_by_event"]:
        raise HTTPException(status_code=400, detail="No photos uploaded yet. Please upload event folders first.")
        
    spreads = spread_engine.create_spreads_from_events(
        event_photos_map=SESSION_STATE["photos_by_event"],
        theme_id=theme_id
    )
    
    for spread in spreads:
        spread_renderer.render_spread(spread, save_preview=True)
        
    SESSION_STATE["spreads"] = spreads
    
    return {
        "message": f"AI composed {len(spreads)} spreads (10800x3600 @ 300 DPI)",
        "spreads": [s.dict() for s in spreads]
    }

@app.get("/api/spreads")
async def get_spreads():
    return {
        "spreads": [s.dict() for s in SESSION_STATE["spreads"]],
        "total_spreads": len(SESSION_STATE["spreads"])
    }

@app.post("/api/export-pdf")
async def export_pdf(album_title: str = "Royal Wedding Photobook"):
    """
    Compiles all generated spreads (10800x3600 @ 300 DPI) into a multi-page PDF.
    """
    if not SESSION_STATE["spreads"]:
        raise HTTPException(status_code=400, detail="No spreads to export.")
        
    spread_paths = []
    for s in SESSION_STATE["spreads"]:
        if s.high_res_url:
            filename = Path(s.high_res_url).name
            full_path = str(EXPORTS_DIR / filename)
            spread_paths.append(full_path)
            
    pdf_path = pdf_generator.create_album_pdf(spread_paths, album_title=album_title)
    pdf_filename = Path(pdf_path).name
    
    SESSION_STATE["last_pdf_path"] = pdf_path
    SESSION_STATE["last_pdf_filename"] = pdf_filename
    
    return {
        "message": "300 DPI High-Resolution PDF Generated Successfully",
        "pdf_filename": pdf_filename,
        "download_url": f"/api/download-pdf/{pdf_filename}",
        "total_pages": len(spread_paths),
        "dimensions": "36\" x 12\" @ 300 DPI (10800 x 3600 px)"
    }

@app.get("/api/download-pdf/{filename}")
async def download_pdf(filename: str):
    file_path = EXPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
        
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )

@app.post("/api/sample-demo")
async def load_sample_demo():
    """
    Demo generator: only used when the user explicitly clicks the demo button.
    """
    from PIL import Image, ImageDraw
    
    SESSION_STATE["photos_by_event"] = {}
    SESSION_STATE["spreads"] = []
    
    events_data = {
        "001 - Wedding": [
            ("wedding_mandap_panorama.jpg", (130, 180, 220), (230, 220, 200), "Mandap Lake Waterfront"),
            ("wedding_portrait_stairs.jpg", (170, 60, 50), (140, 45, 40), "Couple Portrait"),
            ("wedding_marble_mandap.jpg", (240, 240, 240), (200, 200, 200), "Temple Carved Pillars"),
            ("wedding_reception_shot.jpg", (245, 240, 230), (45, 90, 130), "Couple Ceremony Moments"),
        ]
    }
    
    for event_folder, photo_specs in events_data.items():
        event_dir = UPLOADS_DIR / event_folder
        event_dir.mkdir(parents=True, exist_ok=True)
        SESSION_STATE["photos_by_event"][event_folder] = []
        
        for fname, col1, col2, title in photo_specs:
            img_path = event_dir / fname
            w, h = (3000, 2000) if "panorama" in fname else (1800, 2200)
            demo_img = Image.new("RGB", (w, h), col1)
            draw = ImageDraw.Draw(demo_img)
            
            for y in range(h):
                blend = y / h
                r = int(col1[0] * (1 - blend) + col2[0] * blend)
                g = int(col1[1] * (1 - blend) + col2[1] * blend)
                b = int(col1[2] * (1 - blend) + col2[2] * blend)
                draw.line([(0, y), (w, y)], fill=(r, g, b))
                
            demo_img.save(str(img_path), "JPEG", quality=92)
            
            rel_url = f"/static/uploads/{event_folder}/{fname}"
            photo_item = PhotoItem(
                file_path=str(img_path),
                relative_url=rel_url,
                original_filename=fname,
                event_name=event_folder
            )
            SESSION_STATE["photos_by_event"][event_folder].append(photo_item)
            
    spreads = spread_engine.create_spreads_from_events(
        event_photos_map=SESSION_STATE["photos_by_event"]
    )
    for spread in spreads:
        spread_renderer.render_spread(spread, save_preview=True)
        
    SESSION_STATE["spreads"] = spreads
    
    return {
        "message": f"Demo generated with {len(spreads)} 300 DPI spreads!",
        "spreads": [s.dict() for s in spreads]
    }

@app.post("/api/reset")
async def reset_session():
    SESSION_STATE["photos_by_event"] = {}
    SESSION_STATE["spreads"] = []
    SESSION_STATE["last_pdf_path"] = None
    SESSION_STATE["last_pdf_filename"] = None
    return {"message": "Session reset successfully"}
