# Stage 1: Build stage for dependencies
FROM python:3.11-bookworm AS builder

# Install required build tools (GCC, g++, make) and Rust for building aiosnmp
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for Rust
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN pip install scalene

# Stage 2: Final stage - slimmer image
FROM python:3.11-bookworm

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY ./app /app

# Command to run the application
CMD ["scalene", "--outfile", "/profiles/data_profile.txt", "--profile-interval", "0.1", "main.py"]
