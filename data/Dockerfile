# Use the official lightweight Python image
FROM python:3.11-slim

# Install required dependencies
RUN apt-get update && \
    apt-get install -y gcc g++ make curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Rust
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the working directory
WORKDIR /app

# Copy application files
COPY ./app /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --default-timeout=150 -r requirements.txt

# Command to run the application
CMD ["python", "main.py"]
