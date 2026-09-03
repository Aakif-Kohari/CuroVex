import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import config
from api.ml_loader import ml_loader
from api.routers import auth, explanations, predictions, validation
from api.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Just register paths, DO NOT load heavy models here.
    # This prevents blocking the server startup and missing the port binding window.
    ml_loader.load(config.MODEL_PATH, config.DATA_DIR)
    yield
    # Cleanup on shutdown


app = FastAPI(
    title="CuroVex API",
    description="Explainable AI framework for drug repurposing",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
app.include_router(explanations.router, prefix="/explanations", tags=["explanations"])
app.include_router(validation.router, prefix="/validation", tags=["validation"])


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", version="1.0.0")
