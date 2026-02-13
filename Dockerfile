# Gunakan base image Python yang ringan
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment supaya Python gak bikin file .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependency system untuk psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dulu (biar layer caching optimal)
COPY requirements.txt .

# Install dependency Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh project
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Command untuk menjalankan FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
