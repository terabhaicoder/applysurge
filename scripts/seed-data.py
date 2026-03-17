#!/usr/bin/env python3
"""Seed database with initial data (subscription plans, default templates)."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session_factory
from app.models.billing import SubscriptionPlan
from app.models.email_template import EmailTemplate
from sqlalchemy import select


async def seed_subscription_plans(session):
    """Create default subscription plans."""
    existing = await session.execute(select(SubscriptionPlan))
    if existing.scalars().first():
        print("  Subscription plans already exist, skipping.")
        return

    plans = [
        SubscriptionPlan(
            name="free",
            display_name="Free",
            description="Get started with basic job applications",
            price_monthly=0,
            price_yearly=0,
            applications_per_month=10,
            emails_per_month=5,
            resumes_limit=1,
            job_sources=["linkedin"],
            features=[
                "10 applications/month",
                "LinkedIn Easy Apply",
                "Basic job matching",
                "1 resume",
            ],
        ),
        SubscriptionPlan(
            name="basic",
            display_name="Basic",
            description="For active job seekers",
            price_monthly=1900,  # $19.00
            price_yearly=15900,  # $159.00
            applications_per_month=100,
            emails_per_month=50,
            resumes_limit=3,
            job_sources=["linkedin", "naukri"],
            features=[
                "100 applications/month",
                "LinkedIn + Naukri",
                "AI cover letters",
                "Cold email outreach",
                "3 resumes",
                "Basic analytics",
            ],
        ),
        SubscriptionPlan(
            name="pro",
            display_name="Pro",
            description="Maximum automation for serious job seekers",
            price_monthly=4900,  # $49.00
            price_yearly=39900,  # $399.00
            applications_per_month=500,
            emails_per_month=200,
            resumes_limit=10,
            job_sources=["linkedin", "naukri", "startup_outreach"],
            features=[
                "500 applications/month",
                "All job sources",
                "AI cover letters & emails",
                "Startup outreach",
                "Advanced analytics",
                "10 resumes",
                "Priority support",
                "Follow-up sequences",
                "Live browser view",
            ],
        ),
        SubscriptionPlan(
            name="enterprise",
            display_name="Enterprise",
            description="For teams and agencies",
            price_monthly=9900,  # $99.00
            price_yearly=79900,  # $799.00
            applications_per_month=2000,
            emails_per_month=1000,
            resumes_limit=50,
            job_sources=["linkedin", "naukri", "startup_outreach", "indeed"],
            features=[
                "Unlimited applications",
                "All sources",
                "Team management",
                "API access",
                "Custom integrations",
                "Dedicated support",
                "White-label option",
            ],
        ),
    ]

    for plan in plans:
        session.add(plan)

    await session.commit()
    print(f"  Created {len(plans)} subscription plans.")


async def seed_email_templates(session):
    """Create default email templates."""
    existing = await session.execute(select(EmailTemplate).where(EmailTemplate.user_id.is_(None)))
    if existing.scalars().first():
        print("  Default email templates already exist, skipping.")
        return

    templates = [
        EmailTemplate(
            user_id=None,  # System-wide defaults
            name="Professional Introduction",
            description="A professional cold email for reaching out to hiring managers",
            subject_template="Quick question about {{job_title}} at {{company}}",
            body_template=(
                "Hi {{hiring_manager_name}},\n\n"
                "{{personalized_opener}}\n\n"
                "I'm a {{current_title}} with {{years_experience}} years of experience "
                "in {{relevant_skills}}. I noticed your team at {{company}} is "
                "{{company_context}}, and I believe my background in {{relevant_experience}} "
                "could be valuable.\n\n"
                "{{value_proposition}}\n\n"
                "Would you be open to a brief chat this week?\n\n"
                "Best,\n{{user_name}}"
            ),
            template_type="initial",
            is_default=True,
        ),
        EmailTemplate(
            user_id=None,
            name="Follow-up #1",
            description="First follow-up email (3 days after initial)",
            subject_template="Re: {{original_subject}}",
            body_template=(
                "Hi {{hiring_manager_name}},\n\n"
                "Just circling back on my note from earlier this week. "
                "I also wanted to share {{added_value}} which might be relevant "
                "to what you're building at {{company}}.\n\n"
                "Happy to chat whenever works for you.\n\n"
                "{{user_name}}"
            ),
            template_type="followup_1",
            is_default=True,
        ),
        EmailTemplate(
            user_id=None,
            name="Follow-up #2 (Breakup)",
            description="Final follow-up email (7 days after initial)",
            subject_template="Re: {{original_subject}}",
            body_template=(
                "Hi {{hiring_manager_name}},\n\n"
                "I know you're busy, so I'll keep this short. "
                "If the timing isn't right, totally understand - "
                "no need to respond. But if {{company}} is looking for "
                "someone with {{key_skill}}, I'd love to connect.\n\n"
                "Either way, wishing you and the team well.\n\n"
                "{{user_name}}"
            ),
            template_type="followup_2",
            is_default=True,
        ),
        EmailTemplate(
            user_id=None,
            name="Startup Outreach",
            description="Cold email for startups without specific job postings",
            subject_template="{{personalized_subject}}",
            body_template=(
                "Hi {{contact_name}},\n\n"
                "{{personalized_opener_about_company}}\n\n"
                "I'm a {{current_title}} passionate about {{relevant_industry}}. "
                "I've been following {{company}} and love {{specific_thing_about_company}}.\n\n"
                "{{how_user_can_help}}\n\n"
                "Would love to explore if there's a fit - "
                "even if you're not actively hiring right now.\n\n"
                "{{user_name}}"
            ),
            template_type="initial",
            is_default=True,
        ),
    ]

    for template in templates:
        session.add(template)

    await session.commit()
    print(f"  Created {len(templates)} default email templates.")


async def main():
    """Run all seeders."""
    print("=== Seeding JobPilot Database ===\n")

    async with async_session_factory() as session:
        await seed_subscription_plans(session)
        await seed_email_templates(session)

    print("\n=== Seeding Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
