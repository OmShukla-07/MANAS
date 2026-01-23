# Hugging Face Space - AI Model API Only
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_hf.txt .
RUN pip install --no-cache-dir -r requirements_hf.txt

# Copy API app
COPY app_hf.py .

# Expose port
EXPOSE 7860

# Run FastAPI
CMD ["uvicorn", "app_hf:app", "--host", "0.0.0.0", "--port", "7860"]
