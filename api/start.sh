#!/bin/sh
set -e

if [ -n "$ARTIFACTS_URL" ] && [ ! -f "ml-core/artifacts/gat_link_predictor.pt" ]; then
  echo "Fetching trained artifacts..."
  
  python - <<'PY'
import os, urllib.request, tarfile, shutil

artifact_url = os.environ.get("ARTIFACTS_URL")
tar_path = "/tmp/artifacts.tar.gz"
extract_dir = "/tmp/artifacts-extract"

print(f"Downloading from {artifact_url}...")
urllib.request.urlretrieve(artifact_url, tar_path)

print("Extracting...")
os.makedirs(extract_dir, exist_ok=True)
with tarfile.open(tar_path, "r:gz") as tar:
    tar.extractall(path=extract_dir)

os.makedirs("ml-core/artifacts", exist_ok=True)
os.makedirs("kg-pipeline/data/normalized", exist_ok=True)

for f in os.listdir(extract_dir):
    src = os.path.join(extract_dir, f)
    if f.endswith(".pt"):
        shutil.move(src, os.path.join("ml-core/artifacts", f))
    elif f.endswith(".csv"):
        shutil.move(src, os.path.join("kg-pipeline/data/normalized", f))

shutil.rmtree(extract_dir)
os.remove(tar_path)
print("Artifacts successfully placed.")
PY

fi

echo "Running database migrations..."
cd api && alembic upgrade head && cd ..

echo "Starting API server..."
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
