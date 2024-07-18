FROM --platform=linux/arm64 python:3.11-slim

# Install Rust
RUN apt-get update && apt-get install -y curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Set environment variables for Rust
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy application files
COPY ./app /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --default-timeout=150 -r requirements.txt

CMD ["python", "main.py"]
