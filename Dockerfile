# Stage 1: Base Image for Dependencies
FROM python:3.12-bookworm AS base

# Install build tools and Rust (minimal profile for smaller installation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain 1.83.0 --profile minimal && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Rust environment
ENV PATH="/root/.cargo/bin:${PATH}"

# Set up the working directory for dependencies
WORKDIR /deps
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --use-feature=fast-deps -r requirements.txt

# Clean up build tools to reduce image size
RUN apt-get remove -y gcc g++ make && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Stage 2: Final Image for Web App
FROM python:3.12-slim-bookworm AS webapp

# Copy Python and Rust environments from the base image
COPY --from=base /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=base /root/.cargo /root/.cargo
ENV PATH="/root/.cargo/bin:${PATH}"

# Set up the web app code
WORKDIR /app
COPY ./web /app

# Expose the port for FastAPI
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--reload"]

# Stage 3: Final Image for Data Collection
FROM python:3.12-slim-bookworm AS data_collection

# Copy Python and Rust environments from the base image
COPY --from=base /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=base /root/.cargo /root/.cargo
ENV PATH="/root/.cargo/bin:${PATH}"

# Set up the data collection code
WORKDIR /app
COPY ./dev /app

# Run the data collection container
CMD ["python3", "main.py"]
