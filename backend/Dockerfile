FROM python:3.12-slim

# Install system dependencies for GDAL/Rasterio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    gdal-bin \
    python3-gdal \
    libproj-dev \
    proj-bin \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /workspace

# Copy requirements and install
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . /workspace/

# Expose FastAPI port
EXPOSE 8000

# Default command starts FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
