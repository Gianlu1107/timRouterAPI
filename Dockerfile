FROM python:3.11-slim

# Install Node.js for Stanford Javascript Crypto Library (SJCL) bridge
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    ROUTER_HOST=192.168.1.1 \
    API_PORT=8000 \
    API_HOST=0.0.0.0

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
