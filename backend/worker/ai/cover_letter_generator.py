"""
AI-powered cover letter generation using Anthropic Claude.

Generates personalized, compelling cover letters based on user profile,
job description, and company research.
"""

import logging
import os
from typing import Dict, Any

import anthropic

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


class CoverLetterGenerator:
    """Generates personalized cover letters using Claude AI."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ANTHROPIC_MODEL

    async def generate(
        self,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
        company_info: Dict[str, Any] = None,
        style: str = "professional",
        max_words: int = 300,
    ) -> str:
        """
        Generate a personalized cover letter.

        Args:
            user_profile: User's profile data (name, skills, experience, etc.)
            job_details: Job posting details (title, company, description)
            company_info: Optional company research data
            style: Writing style (professional, conversational, enthusiastic)
            max_words: Maximum word count for the letter

        Returns:
            Generated cover letter text
        """
        try:
            # Build context about the user
            user_context = self._build_user_context(user_profile)

            # Build job context
            job_context = self._build_job_context(job_details)

            # Build company context if available
            company_context = ""
            if company_info:
                company_context = self._build_company_context(company_info)

            prompt = f"""Generate a personalized cover letter for a job application.

USER PROFILE:
{user_context}

JOB DETAILS:
{job_context}

{f"COMPANY INFORMATION:{chr(10)}{company_context}" if company_context else ""}

REQUIREMENTS:
- Style: {style}
- Maximum length: {max_words} words
- Start with a compelling opening that shows genuine interest
- Highlight 2-3 most relevant skills/experiences that match the job
- Show knowledge of the company if information is available
- Include a specific example or achievement that demonstrates capability
- End with enthusiasm and a call to action
- Do NOT include placeholder text like [Your Name] - use the actual name
- Do NOT include the date or address headers
- Keep it concise and impactful
- Avoid generic phrases like "I am writing to express my interest"
- Make it feel authentic and personal, not template-like

Write only the cover letter body text, nothing else."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            cover_letter = response.content[0].text.strip()
            logger.info(f"Generated cover letter ({len(cover_letter.split())} words)")
            return cover_letter

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error generating cover letter: {e}")
            return self._generate_fallback(user_profile, job_details)
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}", exc_info=True)
            return self._generate_fallback(user_profile, job_details)

    def _build_user_context(self, profile: Dict[str, Any]) -> str:
        """Build user context string from profile."""
        parts = []

        if profile.get("full_name"):
            parts.append(f"Name: {profile['full_name']}")
        if profile.get("current_title"):
            parts.append(f"Current Role: {profile['current_title']}")
        if profile.get("current_company"):
            parts.append(f"Current Company: {profile['current_company']}")
        if profile.get("experience_years"):
            parts.append(f"Experience: {profile['experience_years']} years")
        if profile.get("skills"):
            skills = profile["skills"]
            if isinstance(skills, list):
                skills = ", ".join(skills)
            parts.append(f"Key Skills: {skills}")
        if profile.get("education") or profile.get("highest_degree"):
            edu = profile.get("education") or profile.get("highest_degree", "")
            parts.append(f"Education: {edu}")
        if profile.get("bio"):
            parts.append(f"Summary: {profile['bio'][:500]}")
        if profile.get("work_experience"):
            exp = profile["work_experience"]
            if isinstance(exp, str):
                parts.append(f"Work Experience:\n{exp[:1000]}")
        if profile.get("resume_text"):
            # Include relevant portion of resume
            parts.append(f"Resume Highlights:\n{profile['resume_text'][:1500]}")

        return "\n".join(parts) if parts else "No profile data available"

    def _build_job_context(self, job: Dict[str, Any]) -> str:
        """Build job context string."""
        parts = []

        if job.get("title"):
            parts.append(f"Position: {job['title']}")
        if job.get("company"):
            parts.append(f"Company: {job['company']}")
        if job.get("location"):
            parts.append(f"Location: {job['location']}")
        if job.get("job_type"):
            parts.append(f"Type: {job['job_type']}")
        if job.get("description"):
            # Limit description length
            desc = job["description"][:3000]
            parts.append(f"Description:\n{desc}")
        if job.get("skills"):
            parts.append(f"Required Skills: {job['skills']}")

        return "\n".join(parts) if parts else "No job details available"

    def _build_company_context(self, company: Dict[str, Any]) -> str:
        """Build company context string."""
        parts = []

        if company.get("description"):
            parts.append(f"About: {company['description'][:500]}")
        if company.get("mission"):
            parts.append(f"Mission: {company['mission']}")
        if company.get("values"):
            values = company["values"]
            if isinstance(values, list):
                values = ", ".join(values)
            parts.append(f"Values: {values}")
        if company.get("industry"):
            parts.append(f"Industry: {company['industry']}")
        if company.get("size"):
            parts.append(f"Size: {company['size']}")
        if company.get("culture_notes"):
            notes = company["culture_notes"]
            if isinstance(notes, list):
                notes = "; ".join(notes)
            parts.append(f"Culture: {notes}")

        return "\n".join(parts) if parts else ""

    def _generate_fallback(
        self, user_profile: Dict[str, Any], job_details: Dict[str, Any]
    ) -> str:
        """Generate a basic cover letter when AI is unavailable."""
        name = user_profile.get("full_name", "")
        title = job_details.get("title", "the position")
        company = job_details.get("company", "your company")
        skills = user_profile.get("skills", "")
        experience = user_profile.get("experience_years", "several")
        current_title = user_profile.get("current_title", "a professional")

        if isinstance(skills, list):
            skills = ", ".join(skills[:5])

        return (
            f"Dear Hiring Team at {company},\n\n"
            f"I am excited to apply for the {title} position. "
            f"As {current_title} with {experience} years of experience, "
            f"I bring a strong background in {skills or 'relevant technologies'}.\n\n"
            f"My experience aligns well with the requirements of this role, "
            f"and I am confident I can make meaningful contributions to your team. "
            f"I am particularly drawn to {company}'s work and would welcome the "
            f"opportunity to contribute to your mission.\n\n"
            f"I look forward to discussing how my skills and experience can benefit your team.\n\n"
            f"Best regards,\n{name}"
        )
