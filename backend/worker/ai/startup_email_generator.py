"""
AI-powered email generator for startup outreach.

Uses Anthropic Claude (claude-sonnet-4-20250514) to generate highly personalized
cold emails to startups, both for general outreach and specific role interest.

Features:
- Researches company context before writing
- References specific things about the company
- Keeps emails SHORT (under 120 words)
- Generates compelling subject lines
- Supports different tones (professional, casual, enthusiastic)
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import anthropic

logger = logging.getLogger(__name__)


@dataclass
class CompanyContext:
    """Context about a company for email personalization."""
    company_name: str
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_description: Optional[str] = None
    company_size: Optional[str] = None
    company_location: Optional[str] = None
    company_tech_stack: Optional[List[str]] = None
    funding_stage: Optional[str] = None
    funding_amount: Optional[str] = None
    recent_news: Optional[str] = None
    product_description: Optional[str] = None
    discovery_source: Optional[str] = None


@dataclass
class UserContext:
    """Context about the user for email personalization."""
    full_name: str
    email: str
    current_title: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    experience_years: int = 0
    industries: List[str] = field(default_factory=list)
    achievements: Optional[List[str]] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_summary: Optional[str] = None
    desired_roles: List[str] = field(default_factory=list)
    unique_value_prop: Optional[str] = None


@dataclass
class RoleContext:
    """Context about a specific role found on the careers page."""
    title: str
    department: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    location: Optional[str] = None
    is_remote: bool = False
    matched_skills: Optional[List[str]] = None
    match_score: float = 0.0


@dataclass
class GeneratedEmail:
    """Result of email generation."""
    subject: str
    body: str
    email_type: str  # startup_outreach, role_interest
    personalization_notes: Optional[str] = None
    confidence_score: float = 0.0
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "body": self.body,
            "email_type": self.email_type,
            "personalization_notes": self.personalization_notes,
            "confidence_score": self.confidence_score,
            "word_count": self.word_count,
        }


class StartupEmailGenerator:
    """
    Generates personalized cold emails to startups using Claude AI.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _build_company_brief(self, company: CompanyContext) -> str:
        """Build a brief about the company for the AI prompt."""
        parts = [f"Company: {company.company_name}"]
        if company.company_industry:
            parts.append(f"Industry: {company.company_industry}")
        if company.company_description:
            parts.append(f"Description: {company.company_description}")
        if company.company_size:
            parts.append(f"Team size: {company.company_size}")
        if company.company_location:
            parts.append(f"Location: {company.company_location}")
        if company.company_tech_stack:
            parts.append(f"Tech stack: {', '.join(company.company_tech_stack)}")
        if company.funding_stage:
            parts.append(f"Funding stage: {company.funding_stage}")
        if company.funding_amount:
            parts.append(f"Funding: {company.funding_amount}")
        if company.recent_news:
            parts.append(f"Recent news: {company.recent_news}")
        if company.product_description:
            parts.append(f"Product: {company.product_description}")
        if company.discovery_source:
            parts.append(f"Found on: {company.discovery_source}")
        if company.company_website:
            parts.append(f"Website: {company.company_website}")
        return "\n".join(parts)

    def _build_user_brief(self, user: UserContext) -> str:
        """Build a brief about the user for the AI prompt."""
        parts = [f"Name: {user.full_name}"]
        if user.current_title:
            parts.append(f"Current title: {user.current_title}")
        if user.skills:
            parts.append(f"Key skills: {', '.join(user.skills[:10])}")
        if user.experience_years:
            parts.append(f"Experience: {user.experience_years} years")
        if user.industries:
            parts.append(f"Industry experience: {', '.join(user.industries)}")
        if user.achievements:
            parts.append(f"Key achievements: {'; '.join(user.achievements[:3])}")
        if user.resume_summary:
            parts.append(f"Summary: {user.resume_summary}")
        if user.desired_roles:
            parts.append(f"Looking for: {', '.join(user.desired_roles)}")
        if user.unique_value_prop:
            parts.append(f"Unique value: {user.unique_value_prop}")
        if user.portfolio_url:
            parts.append(f"Portfolio: {user.portfolio_url}")
        if user.linkedin_url:
            parts.append(f"LinkedIn: {user.linkedin_url}")
        return "\n".join(parts)

    async def generate_startup_outreach_email(
        self,
        company: CompanyContext,
        user: UserContext,
        contact_name: Optional[str] = None,
        contact_title: Optional[str] = None,
        tone: str = "professional",
        custom_instructions: Optional[str] = None,
    ) -> GeneratedEmail:
        """
        Generate a cold outreach email for a startup with no specific job posting.

        This email:
        - References specific things about the company (product, mission, launch)
        - Pitches the user's value without referencing a specific role
        - Suggests how user's skills can help the company grow
        - Stays under 120 words

        Args:
            company: Company context for personalization.
            user: User context for self-presentation.
            contact_name: Name of the person being emailed.
            contact_title: Title of the contact.
            tone: Email tone (professional, casual, enthusiastic).
            custom_instructions: Optional custom instructions for generation.

        Returns:
            GeneratedEmail with subject line and body.
        """
        company_brief = self._build_company_brief(company)
        user_brief = self._build_user_brief(user)

        greeting = f"Hi {contact_name.split()[0]}," if contact_name else "Hi,"
        contact_context = ""
        if contact_name and contact_title:
            contact_context = f"\nRecipient: {contact_name}, {contact_title} at {company.company_name}"

        tone_guidance = {
            "professional": "Keep the tone professional but warm. Be concise and direct.",
            "casual": "Keep the tone friendly and conversational. Be approachable but still competent.",
            "enthusiastic": "Show genuine excitement about the company's work. Be energetic but not over-the-top.",
        }

        prompt = f"""You are writing a cold outreach email to a startup. The goal is to express interest in working there even though there's no specific job posting.

CRITICAL RULES:
1. The email body MUST be under 120 words. This is non-negotiable.
2. Reference something SPECIFIC about the company (their product, mission, recent launch, tech stack).
3. Do NOT reference a specific job posting or role title.
4. Pitch the sender's value in terms of how they can help the company grow.
5. Make it feel personal and researched, not templated.
6. Include a clear but soft call-to-action (like a quick chat).
7. Do NOT start with "I hope this email finds you well" or similar cliches.
8. Do NOT use phrases like "I came across" or "I stumbled upon."
9. {tone_guidance.get(tone, tone_guidance["professional"])}
10. Start the email body with "{greeting}"

COMPANY INFORMATION:
{company_brief}
{contact_context}

SENDER INFORMATION:
{user_brief}

{f"CUSTOM INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

Generate the email in the following exact format:
SUBJECT: [subject line here]
BODY:
[email body here - under 120 words]

The subject line should be:
- Short (under 8 words)
- Specific to the company (mention their name or product)
- NOT generic like "Opportunity" or "Quick question"
- Intriguing enough to open"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            response_text = response.content[0].text.strip()

            # Parse subject and body
            subject, body = self._parse_email_response(response_text)

            # Add portfolio link if configured
            if user.portfolio_url:
                body += f"\n\n{user.portfolio_url}"

            # Calculate word count
            word_count = len(body.split())

            # If over 120 words, regenerate with stricter instructions
            if word_count > 140:
                logger.warning(f"Email too long ({word_count} words), regenerating...")
                subject, body = await self._regenerate_shorter(
                    company, user, contact_name, greeting, tone
                )
                word_count = len(body.split())

            return GeneratedEmail(
                subject=subject,
                body=body,
                email_type="startup_outreach",
                personalization_notes=self._identify_personalization(body, company),
                confidence_score=self._calculate_confidence(body, company, user),
                word_count=word_count,
            )

        except Exception as e:
            logger.error(f"Error generating startup outreach email: {e}")
            # Return a minimal fallback email
            return self._generate_fallback_outreach(company, user, contact_name, greeting)

    async def generate_role_interest_email(
        self,
        company: CompanyContext,
        user: UserContext,
        role: RoleContext,
        contact_name: Optional[str] = None,
        contact_title: Optional[str] = None,
        tone: str = "professional",
        custom_instructions: Optional[str] = None,
    ) -> GeneratedEmail:
        """
        Generate an email expressing interest in a specific role found on the careers page.

        This email:
        - References the specific role found on their careers page
        - Shows alignment between user's experience and the role requirements
        - More targeted and specific than generic outreach
        - Still keeps it concise (under 150 words)

        Args:
            company: Company context.
            user: User context.
            role: Role context from careers page.
            contact_name: Name of the contact.
            contact_title: Title of the contact.
            tone: Email tone.
            custom_instructions: Optional custom instructions.

        Returns:
            GeneratedEmail with subject and body.
        """
        company_brief = self._build_company_brief(company)
        user_brief = self._build_user_brief(user)

        greeting = f"Hi {contact_name.split()[0]}," if contact_name else "Hi,"
        contact_context = ""
        if contact_name and contact_title:
            contact_context = f"\nRecipient: {contact_name}, {contact_title}"

        # Build role brief
        role_parts = [f"Role: {role.title}"]
        if role.department:
            role_parts.append(f"Department: {role.department}")
        if role.description:
            role_parts.append(f"Description: {role.description[:300]}")
        if role.requirements:
            role_parts.append(f"Requirements: {'; '.join(role.requirements[:5])}")
        if role.matched_skills:
            role_parts.append(f"Matching skills: {', '.join(role.matched_skills)}")
        if role.location:
            role_parts.append(f"Location: {role.location}")
        role_brief = "\n".join(role_parts)

        tone_guidance = {
            "professional": "Professional and confident, showing clear fit.",
            "casual": "Friendly and conversational, naturally showing alignment.",
            "enthusiastic": "Excited about the role, showing genuine passion for the match.",
        }

        prompt = f"""You are writing a targeted email to a startup about a specific role you found on their careers page.

CRITICAL RULES:
1. The email body MUST be under 150 words.
2. Reference the SPECIFIC ROLE by name that you found on their careers/jobs page.
3. Show clear alignment between the sender's experience and the role requirements.
4. Mention 2-3 specific skills or experiences that make them a fit.
5. Include a call-to-action (express desire to discuss further).
6. Do NOT start with cliches.
7. {tone_guidance.get(tone, tone_guidance["professional"])}
8. Start the email body with "{greeting}"

COMPANY INFORMATION:
{company_brief}
{contact_context}

ROLE FOUND ON CAREERS PAGE:
{role_brief}

SENDER INFORMATION:
{user_brief}

{f"CUSTOM INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

Generate the email in the following exact format:
SUBJECT: [subject line - reference the role]
BODY:
[email body here - under 150 words]

The subject line should:
- Mention the role title
- Be specific and direct
- Under 10 words"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            response_text = response.content[0].text.strip()
            subject, body = self._parse_email_response(response_text)

            # Add portfolio link if configured
            if user.portfolio_url:
                body += f"\n\n{user.portfolio_url}"

            word_count = len(body.split())

            return GeneratedEmail(
                subject=subject,
                body=body,
                email_type="role_interest",
                personalization_notes=self._identify_personalization(body, company),
                confidence_score=self._calculate_confidence(body, company, user),
                word_count=word_count,
            )

        except Exception as e:
            logger.error(f"Error generating role interest email: {e}")
            return self._generate_fallback_role_interest(company, user, role, contact_name, greeting)

    def _parse_email_response(self, response_text: str) -> tuple:
        """Parse the AI response into subject and body."""
        subject = ""
        body = ""

        lines = response_text.split("\n")
        body_started = False

        for line in lines:
            if line.strip().upper().startswith("SUBJECT:"):
                subject = line.split(":", 1)[1].strip()
                # Remove quotes if present
                subject = subject.strip('"').strip("'")
            elif line.strip().upper() == "BODY:" or line.strip().upper().startswith("BODY:"):
                body_started = True
                # Check if body content is on same line
                remainder = line.split(":", 1)[1].strip() if ":" in line else ""
                if remainder:
                    body = remainder + "\n"
            elif body_started:
                body += line + "\n"

        body = body.strip()

        # Fallback parsing if format wasn't followed
        if not subject and not body:
            # Try to split on first newline after a short first line
            lines = response_text.strip().split("\n")
            if lines:
                first_line = lines[0].strip()
                if len(first_line) < 100 and not first_line.startswith("Hi"):
                    subject = first_line.strip('"').strip("'")
                    body = "\n".join(lines[1:]).strip()
                else:
                    subject = f"Interest in {lines[0][:50]}"
                    body = response_text.strip()

        if not subject:
            subject = "Quick note about joining your team"

        return subject, body

    async def _regenerate_shorter(
        self,
        company: CompanyContext,
        user: UserContext,
        contact_name: Optional[str],
        greeting: str,
        tone: str,
    ) -> tuple:
        """Regenerate email with stricter length constraints."""
        prompt = f"""Rewrite this as an ultra-concise cold email to {company.company_name}.
MAXIMUM 100 words. Start with "{greeting}"
Sender: {user.full_name}, {user.current_title or 'experienced professional'} with skills in {', '.join(user.skills[:5])}.
Company does: {company.company_description or company.company_industry or 'technology'}.
Tone: {tone}.
Show you know what they do. Pitch your value. Ask for a quick chat.

Format:
SUBJECT: [short subject]
BODY:
[ultra-concise email under 100 words]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_email_response(response.content[0].text.strip())
        except Exception:
            return self._generate_fallback_outreach(company, user, contact_name, greeting).subject, self._generate_fallback_outreach(company, user, contact_name, greeting).body

    def _identify_personalization(self, body: str, company: CompanyContext) -> str:
        """Identify what personalization elements are in the email."""
        elements = []
        body_lower = body.lower()

        if company.company_name and company.company_name.lower() in body_lower:
            elements.append("company_name")
        if company.company_industry and company.company_industry.lower() in body_lower:
            elements.append("industry")
        if company.company_tech_stack:
            for tech in company.company_tech_stack:
                if tech.lower() in body_lower:
                    elements.append(f"tech:{tech}")
                    break
        if company.product_description:
            # Check if any product-related words are mentioned
            product_words = company.product_description.lower().split()[:5]
            if any(w in body_lower for w in product_words if len(w) > 4):
                elements.append("product_reference")
        if company.funding_stage and company.funding_stage.lower() in body_lower:
            elements.append("funding")

        return ", ".join(elements) if elements else "minimal"

    def _calculate_confidence(
        self, body: str, company: CompanyContext, user: UserContext
    ) -> float:
        """Calculate confidence score for the generated email."""
        score = 0.5  # Base score

        # Check word count (ideal: 60-120 words)
        word_count = len(body.split())
        if 60 <= word_count <= 120:
            score += 0.1
        elif word_count > 150:
            score -= 0.2

        # Check personalization
        body_lower = body.lower()
        if company.company_name and company.company_name.lower() in body_lower:
            score += 0.1
        if company.company_tech_stack and any(
            t.lower() in body_lower for t in company.company_tech_stack
        ):
            score += 0.1

        # Check if user skills are mentioned
        if user.skills and any(s.lower() in body_lower for s in user.skills[:5]):
            score += 0.1

        # Check for CTA
        cta_keywords = ["chat", "call", "coffee", "connect", "discuss", "talk", "meet"]
        if any(kw in body_lower for kw in cta_keywords):
            score += 0.05

        # Penalize cliches
        cliches = ["hope this finds you", "reaching out", "i came across", "i stumbled upon"]
        if any(c in body_lower for c in cliches):
            score -= 0.15

        return max(0.0, min(1.0, score))

    def _generate_fallback_outreach(
        self,
        company: CompanyContext,
        user: UserContext,
        contact_name: Optional[str],
        greeting: str,
    ) -> GeneratedEmail:
        """Generate a simple fallback email if AI generation fails."""
        subject = f"Interest in {company.company_name}"

        skills_text = ", ".join(user.skills[:3]) if user.skills else "my expertise"
        company_desc = company.company_industry or "your work"

        body = f"""{greeting}

I've been following {company.company_name}'s work in {company_desc} and I'm impressed by what you're building.

With {user.experience_years}+ years of experience in {skills_text}, I'd love to explore how I could contribute to your team's growth.

Would you be open to a brief chat this week?

Best,
{user.full_name}"""

        if user.portfolio_url:
            body += f"\n{user.portfolio_url}"

        return GeneratedEmail(
            subject=subject,
            body=body.strip(),
            email_type="startup_outreach",
            personalization_notes="fallback_template",
            confidence_score=0.3,
            word_count=len(body.split()),
        )

    def _generate_fallback_role_interest(
        self,
        company: CompanyContext,
        user: UserContext,
        role: RoleContext,
        contact_name: Optional[str],
        greeting: str,
    ) -> GeneratedEmail:
        """Generate a simple fallback email for role interest."""
        subject = f"Re: {role.title} at {company.company_name}"

        matched = ", ".join(role.matched_skills[:3]) if role.matched_skills else ", ".join(user.skills[:3])

        body = f"""{greeting}

I noticed the {role.title} role on your careers page and I'm very interested. My background in {matched} aligns well with what you're looking for.

I have {user.experience_years}+ years of relevant experience and I'd love to discuss how I can contribute to your {role.department or 'team'}.

Are you available for a quick conversation this week?

Best,
{user.full_name}"""

        if user.portfolio_url:
            body += f"\n{user.portfolio_url}"

        return GeneratedEmail(
            subject=subject,
            body=body.strip(),
            email_type="role_interest",
            personalization_notes="fallback_template",
            confidence_score=0.3,
            word_count=len(body.split()),
        )


async def generate_startup_outreach_email(
    company_data: Dict[str, Any],
    user_data: Dict[str, Any],
    contact_name: Optional[str] = None,
    contact_title: Optional[str] = None,
    tone: str = "professional",
    custom_instructions: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High-level function to generate a startup outreach email.

    Args:
        company_data: Dictionary with company information.
        user_data: Dictionary with user information.
        contact_name: Name of the contact person.
        contact_title: Title of the contact.
        tone: Email tone.
        custom_instructions: Custom instructions for generation.
        api_key: Optional Anthropic API key override.

    Returns:
        Dictionary with generated email data.
    """
    company = CompanyContext(
        company_name=company_data.get("company_name", ""),
        company_website=company_data.get("company_website"),
        company_industry=company_data.get("company_industry"),
        company_description=company_data.get("company_description"),
        company_size=company_data.get("company_size"),
        company_location=company_data.get("company_location"),
        company_tech_stack=company_data.get("company_tech_stack"),
        funding_stage=company_data.get("funding_stage"),
        funding_amount=company_data.get("funding_amount"),
        recent_news=company_data.get("recent_news"),
        product_description=company_data.get("product_description"),
        discovery_source=company_data.get("discovery_source"),
    )

    user = UserContext(
        full_name=user_data.get("full_name", ""),
        email=user_data.get("email", ""),
        current_title=user_data.get("current_title"),
        skills=user_data.get("skills", []),
        experience_years=user_data.get("experience_years", 0),
        industries=user_data.get("industries", []),
        achievements=user_data.get("achievements"),
        portfolio_url=user_data.get("portfolio_url"),
        linkedin_url=user_data.get("linkedin_url"),
        resume_summary=user_data.get("resume_summary"),
        desired_roles=user_data.get("desired_roles", []),
        unique_value_prop=user_data.get("unique_value_prop"),
    )

    generator = StartupEmailGenerator(api_key=api_key)
    email = await generator.generate_startup_outreach_email(
        company=company,
        user=user,
        contact_name=contact_name,
        contact_title=contact_title,
        tone=tone,
        custom_instructions=custom_instructions,
    )
    return email.to_dict()


async def generate_role_interest_email(
    company_data: Dict[str, Any],
    user_data: Dict[str, Any],
    role_data: Dict[str, Any],
    contact_name: Optional[str] = None,
    contact_title: Optional[str] = None,
    tone: str = "professional",
    custom_instructions: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High-level function to generate a role interest email.

    Args:
        company_data: Dictionary with company information.
        user_data: Dictionary with user information.
        role_data: Dictionary with role information.
        contact_name: Name of the contact.
        contact_title: Title of the contact.
        tone: Email tone.
        custom_instructions: Custom instructions.
        api_key: Optional Anthropic API key override.

    Returns:
        Dictionary with generated email data.
    """
    company = CompanyContext(
        company_name=company_data.get("company_name", ""),
        company_website=company_data.get("company_website"),
        company_industry=company_data.get("company_industry"),
        company_description=company_data.get("company_description"),
        company_size=company_data.get("company_size"),
        company_location=company_data.get("company_location"),
        company_tech_stack=company_data.get("company_tech_stack"),
        funding_stage=company_data.get("funding_stage"),
        product_description=company_data.get("product_description"),
    )

    user = UserContext(
        full_name=user_data.get("full_name", ""),
        email=user_data.get("email", ""),
        current_title=user_data.get("current_title"),
        skills=user_data.get("skills", []),
        experience_years=user_data.get("experience_years", 0),
        industries=user_data.get("industries", []),
        achievements=user_data.get("achievements"),
        portfolio_url=user_data.get("portfolio_url"),
        linkedin_url=user_data.get("linkedin_url"),
        resume_summary=user_data.get("resume_summary"),
        desired_roles=user_data.get("desired_roles", []),
        unique_value_prop=user_data.get("unique_value_prop"),
    )

    role = RoleContext(
        title=role_data.get("title", ""),
        department=role_data.get("department"),
        description=role_data.get("description"),
        requirements=role_data.get("requirements"),
        location=role_data.get("location"),
        is_remote=role_data.get("is_remote", False),
        matched_skills=role_data.get("matched_skills"),
        match_score=role_data.get("match_score", 0.0),
    )

    generator = StartupEmailGenerator(api_key=api_key)
    email = await generator.generate_role_interest_email(
        company=company,
        user=user,
        role=role,
        contact_name=contact_name,
        contact_title=contact_title,
        tone=tone,
        custom_instructions=custom_instructions,
    )
    return email.to_dict()
