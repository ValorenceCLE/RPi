FROM python:3.11-slim

WORKDIR /app

# Copy application files
COPY ./app /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --default-timeout=150 --no-cache-dir -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
