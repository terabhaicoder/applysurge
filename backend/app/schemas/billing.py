"""
Billing and subscription schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanResponse(BaseModel):
    """Schema for subscription plan."""
    id: str
    name: str
    description: str
    price_monthly: float
    price_yearly: Optional[float] = None
    features: List[str] = []
    limits: dict = {}
    is_popular: bool = False


class SubscriptionResponse(BaseModel):
    """Schema for user subscription."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    user_id: UUID
    plan: str = "free"
    status: str = "active"  # active, cancelled, past_due, trialing
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: Optional[datetime] = None


class CheckoutRequest(BaseModel):
    """Schema for creating checkout session."""
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Schema for checkout session response."""
    checkout_url: str
    session_id: str


class PortalRequest(BaseModel):
    """Schema for creating billing portal session."""
    return_url: str


class PortalResponse(BaseModel):
    """Schema for billing portal response."""
    portal_url: str
