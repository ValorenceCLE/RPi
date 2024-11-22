# Stage 1: Build stage for dependencies
FROM python:3.11-bookworm AS base

# Install build tools and Rust (Needed for aiosnmp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Rust Environment
ENV PATH="/root/.cargo/bin:${PATH}"

# Set a virtual environment for dependencies
WORKDIR /deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Stage 2: Final stage for web app
FROM python:3.11-slim-bookworm as webapp

# Copy virtual environment from the base image
COPY --from=base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up the web app code
WORKDIR /app
COPY ./web/app /app

# Expose the port for FastAPI
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--reload"]


# Stage 3: Final stage for data collection
FROM python:3.11-slim-bookworm as data_collection

# Copy virtual environment from the base image
COPY --from=base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up the data collection code
WORKDIR /app
COPY ./dev/app /app

# Run the data collection container
CMD ["python3", "main.py"]