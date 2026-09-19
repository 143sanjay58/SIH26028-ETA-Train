from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    Index,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(20), nullable=False)  # BASELINE, STATISTICAL, ML
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)  # XGBOOST, LIGHTGBM, RF, etc.
    
    # Model artifacts
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    scaler_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    feature_names: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    
    # Training metadata
    training_data_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_data_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_samples: Mapped[int] = mapped_column(Integer, default=0)
    validation_samples: Mapped[int] = mapped_column(Integer, default=0)
    test_samples: Mapped[int] = mapped_column(Integer, default=0)
    
    # Hyperparameters
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=False)
    is_deployed: Mapped[bool] = mapped_column(default=False)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    metrics: Mapped[list["ModelMetrics"]] = relationship("ModelMetrics", back_populates="model_version")

    __table_args__ = (
        Index("ix_model_versions_type_active", "model_type", "is_active"),
        Index("ix_model_versions_deployed", "is_deployed"),
    )


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False, index=True)
    
    # Dataset split
    dataset_split: Mapped[str] = mapped_column(String(20), nullable=False)  # TRAIN, VALIDATION, TEST
    
    # Regression metrics
    mae: Mapped[float] = mapped_column(Float, nullable=False)
    rmse: Mapped[float] = mapped_column(Float, nullable=False)
    r2: Mapped[float] = mapped_column(Float, nullable=False)
    median_absolute_error: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Accuracy within thresholds
    accuracy_within_5min: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_within_10min: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_within_15min: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Latency
    avg_prediction_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    p95_prediction_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Feature importance
    feature_importance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Additional metrics
    additional_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", back_populates="metrics")

    __table_args__ = (
        Index("ix_model_metrics_version_split", "model_version_id", "dataset_split"),
    )