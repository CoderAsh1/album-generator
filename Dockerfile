FROM python:3.10-slim

# Hugging Face Spaces run as a non-root user for security
RUN useradd -m -u 1000 user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Install system dependencies if required by any python packages (like opencv)
USER root
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
USER user

# Copy the requirements file first to leverage Docker cache
COPY --chown=user:user backend/requirements.txt $HOME/app/backend/

# Install the Python dependencies
RUN pip install --no-cache-dir -r $HOME/app/backend/requirements.txt

# Copy the rest of the application code
COPY --chown=user:user backend $HOME/app/backend

# Ensure directories exist and are writable
RUN mkdir -p $HOME/app/backend/storage $HOME/app/backend/data

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Start the FastAPI application on port 7860
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "7860"]
