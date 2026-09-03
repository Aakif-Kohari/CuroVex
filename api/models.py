import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    saved_searches = relationship("SavedSearch", back_populates="user")
    prediction_runs = relationship("PredictionRun", back_populates="user")

class SavedSearch(Base):
    __tablename__ = "saved_searches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    disease_query = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="saved_searches")

class PredictionRun(Base):
    __tablename__ = "prediction_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    disease_id = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="prediction_runs")
    predictions = relationship("Prediction", back_populates="run", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("prediction_runs.id"), nullable=False)
    drug_id = Column(String, nullable=False)
    drug_name = Column(String, nullable=True)
    disease_id = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    
    run = relationship("PredictionRun", back_populates="predictions")
    explanations = relationship("Explanation", back_populates="prediction", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="prediction", cascade="all, delete-orphan")

class Explanation(Base):
    __tablename__ = "explanations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False)
    method = Column(String, nullable=False)
    fidelity_score = Column(Float, nullable=True)
    subgraph = Column(JSONB, nullable=False)
    
    prediction = relationship("Prediction", back_populates="explanations")

class ValidationResult(Base):
    __tablename__ = "validation_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False)
    has_clinical_trial = Column(Boolean, nullable=False, default=False)
    has_literature_support = Column(Boolean, nullable=False, default=False)
    evidence_url = Column(String, nullable=True)
    
    prediction = relationship("Prediction", back_populates="validation_results")
