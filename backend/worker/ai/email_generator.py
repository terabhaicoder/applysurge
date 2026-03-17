"""
AI-powered email generation.

Generates personalized cold emails and followup emails
for job applications using Claude AI.
"""

import logging
import os
from typing import Dict, Any, Optional

import anthropic

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


class EmailGenerator:
    """Generates cold emails and followups for job applications."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ANTHROPIC_MODEL

    async def generate_cold_email(
        self,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
        cover_letter: str = "",
        company_info: Dict[str, Any] = None,
    ) -> Dict[str, str]:
        """
        Generate a personalized cold email for a job application.

        Args:
            user_profile: User's profile data
            job_details: Job posting details
            cover_letter: Optional cover letter to reference
            company_info: Optional company research

        Returns:
            Dict with 'subject' and 'body' keys
        """
        try:
            profile_context = self._build_profile_context(user_profile)
            job_context = self._build_job_context(job_details)
            company_context = self._build_company_context(company_info) if company_info else ""

            prompt = f"""Generate a cold email to a hiring manager for a job application.

SENDER PROFILE:
{profile_context}

JOB DETAILS:
{job_context}

{f"COMPANY RESEARCH:{chr(10)}{company_context}" if company_context else ""}

{f"COVER LETTER HIGHLIGHTS:{chr(10)}{cover_letter[:500]}" if cover_letter else ""}

REQUIREMENTS:
- Subject line: Catchy, specific, mentions the role
- Opening: Reference something specific about the company (not generic)
- Body: 3-4 sentences max highlighting top 2 relevant qualifications
- Include a specific metric or achievement if possible
- Closing: Clear ask for a conversation, not desperate
- Total length: Under 150 words for the body
- Tone: Professional but warm, not robotic
- Do NOT include placeholder names - use the actual sender name
- Do NOT include the sender's email or phone in the body (it's in the signature)
- Format: Plain text, no HTML or markdown

Respond with JSON:
{{"subject": "Email subject line", "body": "Email body text"}}

Respond ONLY with the JSON object."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            response_text = response.content[0].text.strip()

            # Parse JSON
            import json
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            result = json.loads(response_text)
            logger.info(f"Generated cold email for {job_details.get('company', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Cold email generation failed: {e}", exc_info=True)
            return self._fallback_cold_email(user_profile, job_details)

    async def generate_followup(
        self,
        original_subject: str,
        original_body: str,
        company: str,
        role: str,
        followup_number: int = 1,
        sender_name: str = "",
    ) -> Dict[str, str]:
        """
        Generate a followup email.

        Args:
            original_subject: Subject of the original email
            original_body: Body of the original email
            company: Company name
            role: Job role
            followup_number: Which followup this is (1, 2, or 3)
            sender_name: Sender's name

        Returns:
            Dict with 'subject' and 'body' keys
        """
        try:
            tone_map = {
                1: "polite check-in, brief value add",
                2: "slightly more direct, offer to help with a specific problem",
                3: "final gentle nudge, acknowledge they're busy, leave door open",
            }
            tone = tone_map.get(followup_number, tone_map[1])

            prompt = f"""Generate followup email #{followup_number} for a job application.

ORIGINAL EMAIL:
Subject: {original_subject}
Body: {original_body[:300]}

CONTEXT:
- Company: {company}
- Role: {role}
- Sender: {sender_name}
- This is followup #{followup_number}

TONE GUIDANCE: {tone}

REQUIREMENTS:
- Keep it very short (2-3 sentences)
- Reference the original email naturally
- Add new value or angle (don't just repeat "checking in")
- For followup #1: Brief, add a new relevant insight or achievement
- For followup #2: More direct, offer specific value
- For followup #3: Graceful close, leave the door open
- Don't be pushy or desperate
- Plain text, no HTML

Respond with JSON:
{{"body": "Followup email body"}}

Respond ONLY with the JSON object."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            response_text = response.content[0].text.strip()

            import json
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            result = json.loads(response_text)
            result["subject"] = f"Re: {original_subject}"
            logger.info(f"Generated followup #{followup_number} for {company}")
            return result

        except Exception as e:
            logger.error(f"Followup generation failed: {e}", exc_info=True)
            return self._fallback_followup(company, role, followup_number, sender_name)

    async def generate_response_to_question(
        self,
        original_email: Dict[str, str],
        question_email: Dict[str, str],
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Generate a response to a question received from a recruiter.

        Args:
            original_email: The original cold email sent
            question_email: The question/response received
            user_profile: User's profile data
            job_details: Job details

        Returns:
            Dict with 'subject' and 'body' keys
        """
        try:
            prompt = f"""Generate a response to a recruiter's question about a job application.

ORIGINAL EMAIL SENT:
Subject: {original_email.get('subject', '')}
Body: {original_email.get('body', '')}

RECRUITER'S RESPONSE:
Subject: {question_email.get('subject', '')}
Body: {question_email.get('body', '')}

CANDIDATE PROFILE:
Name: {user_profile.get('full_name', '')}
Current Role: {user_profile.get('current_title', '')}
Experience: {user_profile.get('experience_years', '')} years
Skills: {user_profile.get('skills', '')}
Notice Period: {user_profile.get('notice_period', '30 days')}
Expected Salary: {user_profile.get('expected_salary', 'negotiable')}

JOB:
Role: {job_details.get('title', '')}
Company: {job_details.get('company', '')}

REQUIREMENTS:
- Answer the recruiter's question(s) directly and honestly
- Keep it professional and concise
- Show continued enthusiasm for the role
- If salary is asked, give a range or say "open to discussion"
- Plain text, no HTML

Respond with JSON:
{{"body": "Response email body"}}

Respond ONLY with the JSON object."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )

            response_text = response.content[0].text.strip()
            import json
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            result = json.loads(response_text)
            result["subject"] = f"Re: {question_email.get('subject', original_email.get('subject', ''))}"
            return result

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "subject": f"Re: {question_email.get('subject', '')}",
                "body": (
                    f"Thank you for your response. I'd be happy to discuss further. "
                    f"Would it be convenient to schedule a call?\n\nBest regards,\n"
                    f"{user_profile.get('full_name', '')}"
                ),
            }

    def _build_profile_context(self, profile: Dict[str, Any]) -> str:
        """Build profile context for prompts."""
        parts = []
        if profile.get("full_name"):
            parts.append(f"Name: {profile['full_name']}")
        if profile.get("current_title"):
            parts.append(f"Role: {profile['current_title']}")
        if profile.get("current_company"):
            parts.append(f"Company: {profile['current_company']}")
        if profile.get("experience_years"):
            parts.append(f"Experience: {profile['experience_years']} years")
        if profile.get("skills"):
            skills = profile["skills"]
            if isinstance(skills, list):
                skills = ", ".join(skills[:10])
            parts.append(f"Skills: {skills}")
        if profile.get("bio"):
            parts.append(f"Summary: {profile['bio'][:200]}")
        return "\n".join(parts) if parts else "Professional candidate"

    def _build_job_context(self, job: Dict[str, Any]) -> str:
        """Build job context for prompts."""
        parts = []
        if job.get("title"):
            parts.append(f"Role: {job['title']}")
        if job.get("company"):
            parts.append(f"Company: {job['company']}")
        if job.get("location"):
            parts.append(f"Location: {job['location']}")
        if job.get("description"):
            parts.append(f"Description: {job['description'][:500]}")
        return "\n".join(parts) if parts else "Position at target company"

    def _build_company_context(self, company: Dict[str, Any]) -> str:
        """Build company context for prompts."""
        parts = []
        if company.get("summary"):
            parts.append(f"About: {company['summary']}")
        if company.get("what_they_do"):
            parts.append(f"Products/Services: {company['what_they_do']}")
        if company.get("recent_focus"):
            parts.append(f"Recent Focus: {company['recent_focus']}")
        return "\n".join(parts) if parts else ""

    def _fallback_cold_email(
        self, profile: Dict[str, Any], job: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate fallback cold email when AI is unavailable."""
        name = profile.get("full_name", "")
        title = job.get("title", "the open position")
        company = job.get("company", "your company")
        current_title = profile.get("current_title", "a professional")
        experience = profile.get("experience_years", "several")

        return {
            "subject": f"Interest in {title} role at {company}",
            "body": (
                f"Hi,\n\n"
                f"I came across the {title} opening at {company} and wanted to reach out directly. "
                f"As {current_title} with {experience} years of experience, "
                f"I believe my background aligns well with what you're looking for.\n\n"
                f"I'd love to learn more about the role and share how I could contribute to your team. "
                f"Would you be open to a brief conversation?\n\n"
                f"Best regards,\n{name}"
            ),
        }

    def _fallback_followup(
        self, company: str, role: str, number: int, sender_name: str
    ) -> Dict[str, str]:
        """Generate fallback followup email."""
        bodies = {
            1: (
                f"Hi,\n\nI wanted to follow up on my previous email about the {role} position. "
                f"I remain very interested in the opportunity and would welcome the chance to discuss "
                f"how I can contribute to {company}.\n\nBest,\n{sender_name}"
            ),
            2: (
                f"Hi,\n\nI'm reaching out once more regarding the {role} role. "
                f"I understand you're likely busy, but I'd appreciate even a brief conversation. "
                f"I'm confident I can add value to your team.\n\nBest,\n{sender_name}"
            ),
            3: (
                f"Hi,\n\nI'll keep this brief - I'm still very interested in the {role} position at {company}. "
                f"If the timing isn't right, I completely understand. Feel free to reach out whenever it makes sense.\n\n"
                f"Wishing you all the best,\n{sender_name}"
            ),
        }

        return {
            "subject": f"Re: Interest in {role} role at {company}",
            "body": bodies.get(number, bodies[1]),
        }
