import sys
from pathlib import Path

# Add backend directory to sys.path so its internal imports work
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

import spaces
from backend.main import app

# ZeroGPU strictly requires at least one function to be decorated with @spaces.GPU.
# Since we are exposing a pure FastAPI app, we add a dummy endpoint here.
@app.get("/api/gpu-ping")
@spaces.GPU
def gpu_ping():
    return {"status": "GPU is awake!"}
