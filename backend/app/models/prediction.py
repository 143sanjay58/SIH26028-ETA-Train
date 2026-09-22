from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class PredictionModelType(str):
    BASELINE = "BASELINE"
    STATISTICAL = "STATISTICAL"
    ML = "ML"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(20), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Prediction targets
    predicted_arrival_delay_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_departure_delay_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_remaining_time_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Uncertainty
    prediction_interval_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prediction_interval_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Features used
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    feature_importance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    prediction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_current: Mapped[bool] = mapped_column(default=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    train: Mapped["Train"] = relationship("Train", back_populates="predictions")
    station: Mapped["Station"] = relationship("Station")
    explanations: Mapped[list["PredictionExplanation"]] = relationship("PredictionExplanation", back_populates="prediction")

    __table_args__ = (
        Index("ix_predictions_train_station_time", "train_id", "station_id", "prediction_time"),
        Index("ix_predictions_current", "train_id", "is_current"),
    )


class PredictionExplanation(Base):
    __tablename__ = "prediction_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False, index=True)
    factor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    factor_value: Mapped[float] = mapped_column(Float, nullable=False)
    contribution_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # POSITIVE, NEGATIVE, NEUTRAL
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="explanations")

    __table_args__ = (
        Index("ix_prediction_explanations_prediction", "prediction_id"),
    )