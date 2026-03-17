"""
Stripe payment service for checkout sessions, portal, and webhooks.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import PaymentError, NotFoundError
from app.models.user import User
from app.models.billing import SubscriptionPlan
from app.schemas.billing import (
    PlanResponse,
    SubscriptionResponse,
    CheckoutResponse,
    PortalResponse,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = [
    PlanResponse(
        id="free",
        name="Free",
        description="Get started with basic features",
        price_monthly=0,
        features=[
            "5 job applications per day",
            "1 resume upload",
            "Basic job matching",
            "Email notifications",
        ],
        limits={
            "applications_daily": 5,
            "applications_monthly": 50,
            "resumes": 1,
            "agent_sessions": 0,
        },
    ),
    PlanResponse(
        id="pro",
        name="Pro",
        description="Unlock full automation",
        price_monthly=29.99,
        price_yearly=299.99,
        features=[
            "50 job applications per day",
            "5 resume uploads",
            "AI-powered job matching",
            "Automation agent",
            "Cover letter generation",
            "Email integration",
            "Priority support",
        ],
        limits={
            "applications_daily": 50,
            "applications_monthly": 500,
            "resumes": 5,
            "agent_sessions": 3,
        },
        is_popular=True,
    ),
    PlanResponse(
        id="enterprise",
        name="Enterprise",
        description="Maximum power for serious job seekers",
        price_monthly=79.99,
        price_yearly=799.99,
        features=[
            "200 job applications per day",
            "Unlimited resume uploads",
            "Advanced AI matching",
            "Priority automation agent",
            "Custom email templates",
            "Advanced analytics",
            "Dedicated support",
            "API access",
        ],
        limits={
            "applications_daily": 200,
            "applications_monthly": 2000,
            "resumes": -1,
            "agent_sessions": 10,
        },
    ),
]


class StripeService:
    """Service for Stripe payment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_plans(self) -> list[PlanResponse]:
        """Get all available plans."""
        return PLANS

    async def get_subscription(self, user_id: UUID) -> SubscriptionResponse:
        """Get user's current subscription."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return SubscriptionResponse(
                user_id=user_id,
                plan="free",
                status="active",
            )

        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=subscription.plan_name,
            status=subscription.status,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            created_at=subscription.created_at,
        )

    async def create_checkout_session(
        self,
        user_id: UUID,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutResponse:
        """Create a Stripe checkout session."""
        # Get or create Stripe customer
        customer_id = await self._get_or_create_customer(user_id)

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": str(user_id)},
            )

            return CheckoutResponse(
                checkout_url=session.url,
                session_id=session.id,
            )
        except stripe.error.StripeError as e:
            raise PaymentError(f"Failed to create checkout session: {str(e)}")

    async def create_portal_session(
        self, user_id: UUID, return_url: str
    ) -> PortalResponse:
        """Create a Stripe billing portal session."""
        customer_id = await self._get_or_create_customer(user_id)

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return PortalResponse(portal_url=session.url)
        except stripe.error.StripeError as e:
            raise PaymentError(f"Failed to create portal session: {str(e)}")

    async def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except stripe.error.SignatureVerificationError:
            raise PaymentError("Invalid webhook signature")
        except Exception as e:
            raise PaymentError(f"Webhook error: {str(e)}")

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(data)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(data)

        return {"status": "processed", "event_type": event_type}

    async def _get_or_create_customer(self, user_id: UUID) -> str:
        """Get or create a Stripe customer for the user."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id

        # Get user email
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user_id)},
            )

            if not subscription:
                subscription = SubscriptionPlan(
                    user_id=user_id,
                    stripe_customer_id=customer.id,
                    plan_name="free",
                    plan_tier="free",
                    status="active",
                )
                self.db.add(subscription)
            else:
                subscription.stripe_customer_id = customer.id

            await self.db.flush()
            return customer.id
        except stripe.error.StripeError as e:
            raise PaymentError(f"Failed to create Stripe customer: {str(e)}")

    async def _handle_checkout_completed(self, data: dict) -> None:
        """Handle successful checkout."""
        user_id = data.get("metadata", {}).get("user_id")
        subscription_id = data.get("subscription")

        if not user_id or not subscription_id:
            return

        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.user_id == UUID(user_id))
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.stripe_subscription_id = subscription_id
            subscription.status = "active"

            # Determine plan from price
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            price_id = stripe_sub["items"]["data"][0]["price"]["id"]

            if price_id == settings.STRIPE_PRICE_ID_PRO:
                subscription.plan_name = "pro"
                subscription.plan_tier = "pro"
            elif price_id == settings.STRIPE_PRICE_ID_ENTERPRISE:
                subscription.plan_name = "enterprise"
                subscription.plan_tier = "enterprise"

            subscription.current_period_start = datetime.fromtimestamp(
                stripe_sub["current_period_start"], tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_sub["current_period_end"], tz=timezone.utc
            )

            # Update user tier
            user_result = await self.db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = user_result.scalar_one_or_none()
            if user:
                user.subscription_tier = subscription.plan_name

            await self.db.flush()

    async def _handle_subscription_updated(self, data: dict) -> None:
        """Handle subscription update."""
        stripe_sub_id = data.get("id")

        result = await self.db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.stripe_subscription_id == stripe_sub_id
            )
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            return

        subscription.status = data.get("status", "active")
        subscription.cancel_at_period_end = data.get("cancel_at_period_end", False)

        if data.get("current_period_start"):
            subscription.current_period_start = datetime.fromtimestamp(
                data["current_period_start"], tz=timezone.utc
            )
        if data.get("current_period_end"):
            subscription.current_period_end = datetime.fromtimestamp(
                data["current_period_end"], tz=timezone.utc
            )

        await self.db.flush()

    async def _handle_subscription_deleted(self, data: dict) -> None:
        """Handle subscription cancellation."""
        stripe_sub_id = data.get("id")

        result = await self.db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.stripe_subscription_id == stripe_sub_id
            )
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            return

        subscription.status = "cancelled"
        subscription.plan_name = "free"
        subscription.plan_tier = "free"

        # Downgrade user
        user_result = await self.db.execute(
            select(User).where(User.id == subscription.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.subscription_tier = "free"

        await self.db.flush()

    async def _handle_payment_failed(self, data: dict) -> None:
        """Handle failed payment."""
        customer_id = data.get("customer")

        result = await self.db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.stripe_customer_id == customer_id
            )
        )
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.status = "past_due"
            await self.db.flush()
