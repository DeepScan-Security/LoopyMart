"""
User model - Stored in PostgreSQL (SQL).
This is the only model stored in SQL. All other data is in MongoDB.
"""

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    """
    User model for authentication.
    
    Cart items and orders reference user_id but are stored in MongoDB.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Profile fields
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Wallet
    wallet_balance: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    pending_cashback: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    last_cashback_redeem_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Flipkart Black membership
    is_black_member: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    black_member_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Gamification - Daily spin wheel (5 spins per day)
    spin_count_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_spin_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Password reset
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Note: Cart items, orders, KYC, and chat history are stored in MongoDB with user_id reference
