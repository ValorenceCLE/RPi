FROM python:3.11-bookworm

WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY ./app /app


# Install Python dependencies
RUN pip install --upgrade pip && pip install --default-timeout=150 --no-cache-dir -r requirements.txt


# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4"]
