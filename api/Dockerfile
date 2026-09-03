# api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and other native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY api/requirements.txt ./api/
COPY explainability/requirements.txt ./explainability/

ARG CACHEBUST=1
# Install dependencies (both API and the ML/explainability dependencies it relies on)
RUN pip install --no-cache-dir -r api/requirements.txt
RUN pip install --no-cache-dir -r explainability/requirements.txt

# Copy the necessary project directories
COPY api/ ./api/
COPY ml-core/ ./ml-core/
COPY explainability/ ./explainability/
COPY validation/ ./validation/

# Set python path so imports across sibling modules (api -> ml-core) work correctly
ENV PYTHONPATH=/app

EXPOSE 8000

COPY api/start.sh ./start.sh
RUN chmod +x start.sh
CMD ["./start.sh"]
