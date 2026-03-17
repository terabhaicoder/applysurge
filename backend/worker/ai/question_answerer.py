"""
AI-powered screening question answerer.

Uses user profile data and LLM (Gemini/Claude) to intelligently answer
screening questions during job applications.
"""

import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class QuestionAnswerer:
    """Answers screening questions using user profile and AI."""

    def __init__(self):
        self.provider = LLM_PROVIDER
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate LLM client."""
        if self.provider == "gemini" or (GEMINI_API_KEY and not ANTHROPIC_API_KEY):
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.client = genai.GenerativeModel('gemini-2.5-flash')
                self.provider = "gemini"
                logger.info("QuestionAnswerer using Gemini")
            except ImportError:
                logger.error("google-generativeai not installed")
                raise
        else:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
                self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
                self.provider = "anthropic"
                logger.info("QuestionAnswerer using Anthropic")
            except ImportError:
                logger.error("anthropic not installed")
                raise

    async def answer_question(
        self,
        question: str,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
        answer_type: str = "text",
        options: List[str] = None,
    ) -> Optional[str]:
        """
        Answer a screening question based on user profile and job context.

        Args:
            question: The question text
            user_profile: User's profile data
            job_details: Job details for context
            answer_type: Type of answer needed (text, select, radio, number)
            options: Available options for select/radio types

        Returns:
            The answer string or None if unable to answer
        """
        try:
            # First try rule-based answers for common questions
            rule_answer = self._try_rule_based(question, user_profile, answer_type, options)
            if rule_answer is not None:
                return rule_answer

            # Use AI for complex questions
            return await self._ai_answer(
                question, user_profile, job_details, answer_type, options
            )

        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return self._safe_default(question, answer_type, options)

    def _try_rule_based(
        self,
        question: str,
        profile: Dict[str, Any],
        answer_type: str,
        options: List[str] = None,
    ) -> Optional[str]:
        """Try to answer common questions with rule-based logic."""
        q_lower = question.lower().strip()

        # Years of experience
        if any(phrase in q_lower for phrase in [
            "years of experience", "years experience", "how many years",
            "total experience", "work experience"
        ]):
            exp = profile.get("experience_years", 0)
            if answer_type == "text" or answer_type == "number":
                return str(exp)
            if options:
                return self._find_closest_option(str(exp), options)

        # Current salary / expected salary
        if "salary" in q_lower or "ctc" in q_lower or "compensation" in q_lower:
            if "expected" in q_lower or "desired" in q_lower:
                salary = profile.get("expected_salary") or profile.get("max_salary", "")
                if salary:
                    return str(salary)
            else:
                salary = profile.get("current_salary", "")
                if salary:
                    return str(salary)

        # Notice period
        if "notice period" in q_lower or "when can you" in q_lower or "availability" in q_lower:
            notice = profile.get("notice_period", "30 days")
            if options:
                return self._find_closest_option(notice, options)
            return str(notice)

        # Location / city
        if any(phrase in q_lower for phrase in ["current location", "city", "where are you"]):
            city = profile.get("city") or profile.get("location", "")
            if city:
                return city

        # Phone number
        if "phone" in q_lower or "mobile" in q_lower or "contact number" in q_lower:
            return profile.get("phone", "")

        # LinkedIn URL
        if "linkedin" in q_lower:
            return profile.get("linkedin_url", "")

        # GitHub
        if "github" in q_lower:
            return profile.get("github_url", "")

        # Portfolio / website
        if "portfolio" in q_lower or "website" in q_lower:
            return profile.get("portfolio_url", "")

        # Work authorization
        if any(phrase in q_lower for phrase in [
            "authorized to work", "legally authorized", "work authorization",
            "eligible to work"
        ]):
            if options:
                return self._find_yes_option(options, default_yes=True)
            return "Yes"

        # Visa sponsorship
        if "sponsorship" in q_lower or "visa" in q_lower:
            needs_sponsor = profile.get("needs_sponsorship", False)
            if options:
                return self._find_yes_option(options, default_yes=needs_sponsor)
            return "Yes" if needs_sponsor else "No"

        # Willing to relocate
        if "relocat" in q_lower:
            willing = profile.get("willing_to_relocate", True)
            if options:
                return self._find_yes_option(options, default_yes=willing)
            return "Yes" if willing else "No"

        # Remote work
        if "remote" in q_lower or "work from home" in q_lower:
            pref = profile.get("remote_preference", "any")
            if pref in ("remote", "hybrid", "any"):
                if options:
                    return self._find_yes_option(options, default_yes=True)
                return "Yes"
            return "No"

        # Education / degree
        if any(phrase in q_lower for phrase in [
            "highest education", "degree", "qualification", "education level"
        ]):
            degree = profile.get("highest_degree") or profile.get("education", "")
            if degree and options:
                return self._find_closest_option(degree, options)
            return degree or None

        # Gender (if required - prefer not to say)
        if "gender" in q_lower:
            if options:
                prefer_not = [o for o in options if "prefer" in o.lower() or "not" in o.lower()]
                if prefer_not:
                    return prefer_not[0]
                gender = profile.get("gender", "")
                if gender:
                    return self._find_closest_option(gender, options)
            return profile.get("gender", "Prefer not to say")

        return None

    async def _ai_answer(
        self,
        question: str,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
        answer_type: str,
        options: List[str] = None,
    ) -> Optional[str]:
        """Use LLM to answer complex screening questions."""
        try:
            # Build context
            profile_context = self._build_profile_context(user_profile)
            job_context = self._build_job_context(job_details)

            options_text = ""
            if options:
                options_text = f"\nAVAILABLE OPTIONS (must choose one):\n" + \
                    "\n".join(f"- {opt}" for opt in options)

            prompt = f"""You are answering a job application screening question on behalf of a candidate.

CANDIDATE PROFILE:
{profile_context}

JOB BEING APPLIED TO:
{job_context}

QUESTION: {question}
ANSWER TYPE: {answer_type}
{options_text}

RULES:
- Answer honestly based on the candidate's profile
- If the answer type is "number", provide only a number
- If options are provided, respond with EXACTLY one of the listed options (verbatim)
- If the answer type is "text", keep it concise (1-2 sentences max)
- For yes/no questions, lean towards answers that help the candidate get the job
- For experience-related questions, be truthful about years/level
- If you truly cannot determine an answer, respond with the most reasonable default
- Do NOT include any explanation - just the answer itself

Answer:"""

            if self.provider == "gemini":
                import google.generativeai as genai
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=256,
                    temperature=0.3,
                )
                # Use async version to avoid blocking the event loop
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                )
                answer = response.text.strip()
            else:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                answer = response.content[0].text.strip()

            # Validate answer against options if provided
            if options:
                answer = self._validate_option(answer, options)

            logger.info(f"AI answered question: '{question[:50]}...' -> '{answer[:50]}'")
            return answer

        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return self._safe_default(question, answer_type, options)

    def _build_profile_context(self, profile: Dict[str, Any]) -> str:
        """Build concise profile context for the prompt."""
        parts = []
        fields = [
            ("full_name", "Name"),
            ("current_title", "Current Role"),
            ("current_company", "Company"),
            ("experience_years", "Years of Experience"),
            ("skills", "Skills"),
            ("city", "Location"),
            ("highest_degree", "Education"),
            ("notice_period", "Notice Period"),
            ("current_salary", "Current Salary"),
            ("expected_salary", "Expected Salary"),
        ]

        for field, label in fields:
            value = profile.get(field)
            if value:
                if isinstance(value, list):
                    value = ", ".join(value)
                parts.append(f"{label}: {value}")

        return "\n".join(parts) if parts else "Limited profile information available"

    def _build_job_context(self, job: Dict[str, Any]) -> str:
        """Build concise job context."""
        parts = []
        if job.get("title"):
            parts.append(f"Role: {job['title']}")
        if job.get("company"):
            parts.append(f"Company: {job['company']}")
        if job.get("location"):
            parts.append(f"Location: {job['location']}")
        if job.get("skills"):
            parts.append(f"Required Skills: {job['skills']}")
        return "\n".join(parts) if parts else "No job details available"

    def _find_closest_option(self, value: str, options: List[str]) -> str:
        """Find the closest matching option to the given value."""
        value_lower = value.lower().strip()

        # Exact match
        for opt in options:
            if opt.lower().strip() == value_lower:
                return opt

        # Contains match
        for opt in options:
            if value_lower in opt.lower() or opt.lower() in value_lower:
                return opt

        # Numeric matching (for experience, salary)
        try:
            val_num = float(value.replace(",", ""))
            best_opt = None
            best_diff = float("inf")
            for opt in options:
                import re
                nums = re.findall(r"[\d.]+", opt)
                if nums:
                    opt_num = float(nums[0])
                    diff = abs(opt_num - val_num)
                    if diff < best_diff:
                        best_diff = diff
                        best_opt = opt
            if best_opt:
                return best_opt
        except (ValueError, TypeError):
            pass

        return options[0] if options else value

    def _find_yes_option(self, options: List[str], default_yes: bool = True) -> str:
        """Find a Yes or No option from the list."""
        target = "yes" if default_yes else "no"
        for opt in options:
            if opt.lower().strip() == target:
                return opt
            if target in opt.lower():
                return opt
        return options[0] if options else ("Yes" if default_yes else "No")

    def _validate_option(self, answer: str, options: List[str]) -> str:
        """Validate and correct an AI answer to match available options."""
        answer_lower = answer.lower().strip()

        # Exact match
        for opt in options:
            if opt.lower().strip() == answer_lower:
                return opt

        # Partial match
        for opt in options:
            if answer_lower in opt.lower() or opt.lower() in answer_lower:
                return opt

        # Fuzzy match
        best_opt = options[0]
        best_score = 0
        for opt in options:
            answer_words = set(answer_lower.split())
            opt_words = set(opt.lower().split())
            overlap = len(answer_words & opt_words)
            if overlap > best_score:
                best_score = overlap
                best_opt = opt

        return best_opt

    def _safe_default(
        self, question: str, answer_type: str, options: List[str] = None
    ) -> Optional[str]:
        """Provide safe default answers when AI is unavailable."""
        if options:
            for opt in options:
                if opt.lower() in ("yes", "true"):
                    return opt
            return options[0]

        if answer_type == "number":
            return "0"

        return None
