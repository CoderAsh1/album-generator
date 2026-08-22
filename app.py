import os
import sys
from pathlib import Path

# Add backend directory to sys.path so its internal imports work
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

import spaces
import gradio as gr
from backend.main import app as fastapi_app

@spaces.GPU
def wake_up_gpu():
    return "GPU is awake!"

# Gradio needs a dummy interface to recognize this as a valid Space
demo = gr.Blocks()
with demo:
    gr.Markdown("# AI Wedding Album Maker API Backend\n\nThis is a headless backend API serving the React frontend. (16GB RAM ZeroGPU Space)")
    btn = gr.Button("Ping Backend")
    out = gr.Textbox()
    btn.click(fn=wake_up_gpu, inputs=[], outputs=[out])

# Mount FastAPI app onto Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/")
