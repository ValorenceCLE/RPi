FROM --platform=arm64 python:3.11-buster

WORKDIR /app

COPY ./app /app
COPY requirments.txt .
RUN pip install -r requirments.txt

CMD ["python", "main.py"]

