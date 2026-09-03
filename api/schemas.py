from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    drug_id: str
    disease_id: str
    drug_name: str | None = None
    score: float
    rank: int


class PredictionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    disease_id: str
    model_version: str
    started_at: datetime
    completed_at: datetime | None = None
    predictions: list[PredictionOut] = []


class ExplanationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prediction_id: UUID
    method: str
    fidelity_score: float | None = None
    subgraph: Any


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: UUID
    explanations: list[ExplanationOut]


class ValidationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prediction_id: UUID
    has_clinical_trial: bool
    has_literature_support: bool
    evidence_url: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    result: Any | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
