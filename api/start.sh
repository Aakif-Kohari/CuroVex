#!/bin/sh
set -e

if [ -n "$ARTIFACTS_URL" ] && [ ! -f "ml-core/artifacts/gat_link_predictor.pt" ]; then
  echo "Fetching trained artifacts..."
  mkdir -p ml-core/artifacts kg-pipeline/data/normalized /tmp/artifacts-extract
  
  echo "Downloading from $ARTIFACTS_URL"
  curl -sL "$ARTIFACTS_URL" -o /tmp/artifacts.tar.gz
  
  echo "Extracting..."
  tar -xzf /tmp/artifacts.tar.gz -C /tmp/artifacts-extract
  
  # Move files to the exact folder paths the API expects
  mv /tmp/artifacts-extract/*.pt ml-core/artifacts/ 2>/dev/null || true
  mv /tmp/artifacts-extract/*.csv kg-pipeline/data/normalized/ 2>/dev/null || true
  
  rm -rf /tmp/artifacts.tar.gz /tmp/artifacts-extract
  echo "Artifacts successfully placed."
fi

echo "Running database migrations..."
cd api && alembic upgrade head && cd ..

echo "Starting API server..."
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
