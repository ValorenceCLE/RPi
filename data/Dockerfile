FROM --platform=arm64 python:3.11-buster

WORKDIR /app

COPY ./app /app
COPY requirements.txt .
RUN pip install --default-timeout=100 -r requirements.txt

CMD ["python", "main.py"]

