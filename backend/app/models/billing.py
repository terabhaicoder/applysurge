"""
Billing models: SubscriptionPlan and PaymentHistory.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )

    # Plan details
    plan_name: Mapped[str] = mapped_column(String(100), default="free", nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    price_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    # Stripe integration
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_payment_method_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Dates
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Quotas and limits
    max_applications_per_day: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_applications_per_month: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    max_resumes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_job_alerts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_platforms: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ai_credits_monthly: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    ai_credits_remaining: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    storage_limit_mb: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Features
    features: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    feature_flags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Usage tracking
    applications_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_credits_used_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_used_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Coupon/discount
    coupon_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    discount_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Extra
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription_plan")

    def __repr__(self) -> str:
        return f"<SubscriptionPlan(user_id={self.user_id}, plan={self.plan_name}, status={self.status})>"

    def is_quota_available(self, resource: str) -> bool:
        """Check if a specific resource quota is available."""
        if resource == "applications":
            return self.applications_this_month < self.max_applications_per_month
        elif resource == "ai_credits":
            return self.ai_credits_remaining > 0
        elif resource == "storage":
            return self.storage_used_mb < self.storage_limit_mb
        return True

    def use_ai_credit(self, amount: int = 1) -> bool:
        """Consume AI credits if available."""
        if self.ai_credits_remaining >= amount:
            self.ai_credits_remaining -= amount
            self.ai_credits_used_this_month += amount
            return True
        return False


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Payment details
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_type: Mapped[str] = mapped_column(String(50), default="subscription", nullable=False)

    # Stripe details
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_receipt_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    billing_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    billing_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Refund info
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refund_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tax
    tax_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    subtotal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Card info (last 4 digits only)
    card_last_four: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    card_brand: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Invoice
    invoice_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Failure info
    failure_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extra
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payment_history")

    def __repr__(self) -> str:
        return f"<PaymentHistory(id={self.id}, amount={self.amount}, status={self.status})>"
