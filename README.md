# Royal Album Generator (10800 × 3600 @ 300 DPI)

An intelligent, cloud-assisted Wedding Photobook & Album Spread Designer built with a **FastAPI backend** and a **React + Vite Frontend** featuring a **1-click automated upload & auto-download flow**.

---

## 🌟 Key Features

- **Exact Print Specs**: Generates spreads at **10,800 × 3,600 pixels @ 300 DPI** (standard 36" × 12" flush mount album spread).
- **Authentic Indian Wedding Photobook Layout**:
  - Dual-tone background canvas with dynamic event color themes.
  - Large central close-up hero portrait with soft horizontal edge feathering.
  - Multi-frame candid photo grids with white borders & realistic drop shadows.
  - Traditional ornamental filigree divider lines and lower-left typography ribbon badge.
- **AI Visual Harmony (Zero Hardcoding)**:
  - Dynamically extracts dominant aesthetic color palettes directly from uploaded photos.
  - Generates event-tailored, non-repeating poetry and calligraphy.
- **Online Cloud AI Integration**:
  - Integrated with **KIE.ai API** using model `gpt-image-2-image-to-image` for cinematic color grading and backdrop styling.
- **Print-Ready 300 DPI PDF**:
  - Automatically compiles all spreads into a multi-page 36" × 12" flush-mount album PDF.
  - Triggers automatic browser download upon completion.

---

## 🏗️ Project Architecture

```
d:/Code/v2_Album_maker/
├── backend/
│   ├── config.py               # Resolution constants (10800x3600, 300 DPI), API keys
│   ├── main.py                 # FastAPI REST API endpoints
│   └── services/
│       ├── color_ai.py         # Dynamic AI color palette extractor
│       ├── asset_manager.py    # Luxury font loader & vector filigree generator
│       ├── spread_engine.py    # Intelligent event organizer & layout solver
│       ├── renderer.py         # High-res 10800x3600 300DPI Pillow compositor
│       ├── kie_client.py       # KIE.ai cloud AI integration client
│       └── pdf_generator.py    # Multi-page 300 DPI PDF compiler
└── frontend/
    ├── package.json            # React 18, Vite, TailwindCSS, Lucide Icons
    ├── vite.config.js          # Dev proxy to FastAPI backend
    └── src/
        ├── App.jsx             # 1-click upload & auto-download studio UI
        └── index.css           # Glassmorphism and dark luxury styling
```

---

## 🚀 Getting Started

### 1. Backend Setup (.venv)
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pillow reportlab pydantic httpx python-multipart aiofiles numpy opencv-python fonttools

# Start FastAPI backend
python -m uvicorn main:app --app-dir backend --port 8008 --host 127.0.0.1
```

### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173/`** in your browser.
