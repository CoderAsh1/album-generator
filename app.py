import os
import sys
from pathlib import Path

# Add backend directory to sys.path so its internal imports work
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

import gradio as gr
from backend.main import app as fastapi_app

# Gradio needs a dummy interface to recognize this as a valid Space
demo = gr.Blocks()
with demo:
    gr.Markdown("# AI Wedding Album Maker API Backend\n\nThis is a headless backend API serving the React frontend. (16GB RAM Gradio Space)")

# Mount FastAPI app onto Gradio
# Gradio UI will be at "/", while all FastAPI endpoints remain at "/api/..." and "/static/..."
app = gr.mount_gradio_app(fastapi_app, demo, path="/")
