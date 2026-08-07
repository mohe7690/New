FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-amh \
    libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data temp outputs logs

ENV TESSDATA_PREFIX=/app/tessdata
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
