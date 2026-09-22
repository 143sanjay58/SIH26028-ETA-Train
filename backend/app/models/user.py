import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Boolean,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class UserRole(str, enum.Enum):
    PASSENGER = "PASSENGER"
    STATION_STAFF = "STATION_STAFF"
    SUPERVISOR = "SUPERVISOR"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PASSENGER, nullable=False)
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    station: Mapped[Optional["Station"]] = relationship("Station")
    reported_station_reports: Mapped[list["StationReport"]] = relationship("StationReport", foreign_keys="StationReport.reported_by_user_id")
    verified_station_reports: Mapped[list["StationReport"]] = relationship("StationReport", foreign_keys="StationReport.verified_by_user_id")

    __table_args__ = (
        Index("ix_users_role_station", "role", "station_id"),
    )