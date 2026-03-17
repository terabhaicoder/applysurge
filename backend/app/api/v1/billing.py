"""
Billing and subscription endpoints.
"""

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PlanResponse,
    PortalRequest,
    PortalResponse,
    SubscriptionResponse,
)
from app.services.stripe_service import StripeService

router = APIRouter()


@router.get("/plans", response_model=list[PlanResponse])
async def get_plans():
    """Get all available subscription plans."""
    from app.services.stripe_service import PLANS
    return PLANS


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's subscription details."""
    service = StripeService(db)
    return await service.get_subscription(current_user.id)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session for subscription upgrade."""
    service = StripeService(db)
    return await service.create_checkout_session(
        user_id=current_user.id,
        price_id=data.price_id,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
    )


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    data: PortalRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe billing portal session for managing subscription."""
    service = StripeService(db)
    return await service.create_portal_session(
        user_id=current_user.id,
        return_url=data.return_url,
    )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    service = StripeService(db)
    result = await service.handle_webhook(payload, stripe_signature or "")
    return result
