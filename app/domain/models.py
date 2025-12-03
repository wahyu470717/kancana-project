from sqlalchemy import DECIMAL, JSON, TIMESTAMP, BigInteger, Column, Integer, String
from sqlalchemy import Float, Text, DateTime, Boolean, ForeignKey, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nip = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    jabatan = Column(String(255), nullable=True)
    no_telepon = Column(String(20), nullable=True)
    organization = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    status_verifikasi = Column(String(50), default="pending", index=True)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    role_name = Column(String(50), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    token_version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    verified_by_user = relationship("User", remote_side=[id], foreign_keys=[verified_by])
    activity_logs = relationship("ActivityLog", back_populates="user")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="role")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable= False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="password_reset_tokens")
