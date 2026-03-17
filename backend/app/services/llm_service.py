"""
LLM service supporting multiple providers (Gemini, Anthropic).
"""

import json
import logging
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine which provider to use
LLM_PROVIDER = settings.LLM_PROVIDER.lower()
GEMINI_API_KEY = settings.GEMINI_API_KEY
ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY


class LLMService:
    """Service for interacting with LLM APIs (Gemini or Anthropic)."""

    def __init__(self):
        self.provider = LLM_PROVIDER

        if self.provider == "gemini" or (GEMINI_API_KEY and not ANTHROPIC_API_KEY):
            self._init_gemini()
        else:
            self._init_anthropic()

    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self.client = genai.GenerativeModel('gemini-2.5-flash')
            self.provider = "gemini"
            logger.info("LLM Service initialized with Gemini")
        except ImportError:
            logger.error("google-generativeai not installed. Run: pip install google-generativeai")
            raise

    def _init_anthropic(self):
        """Initialize Anthropic async client."""
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            self.model = settings.ANTHROPIC_MODEL
            self.provider = "anthropic"
            logger.info("LLM Service initialized with Anthropic")
        except ImportError:
            logger.error("anthropic not installed")
            raise

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using the configured LLM provider."""
        if self.provider == "gemini":
            return await self._generate_gemini(prompt, system_prompt, max_tokens, temperature)
        else:
            return await self._generate_anthropic(prompt, system_prompt, max_tokens, temperature)

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Gemini."""
        import google.generativeai as genai

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        response = await self.client.generate_content_async(
            full_prompt,
            generation_config=generation_config,
        )
        return response.text

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Anthropic Claude."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def generate_cover_letter(
        self,
        job_title: str,
        company: str,
        job_description: str,
        resume_text: str,
        tone: str = "professional",
    ) -> str:
        """Generate a cover letter tailored to a specific job."""
        system_prompt = """You are an expert career counselor and professional writer.
Generate tailored cover letters that highlight relevant experience and skills.
Be concise, professional, and authentic. Avoid generic phrases."""

        prompt = f"""Write a {tone} cover letter for the following:

Job Title: {job_title}
Company: {company}

Job Description:
{job_description[:3000]}

Applicant's Resume:
{resume_text[:3000]}

Write a compelling cover letter (3-4 paragraphs) that:
1. Shows genuine interest in the specific role and company
2. Highlights 2-3 most relevant experiences/skills from the resume
3. Demonstrates understanding of the job requirements
4. Includes a strong closing with call to action

Do not include placeholder brackets. Write the complete letter."""

        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.7,
        )

    async def generate_application_answers(
        self,
        questions: List[dict],
        resume_text: str,
        job_description: str,
    ) -> List[dict]:
        """Generate answers for job application questions."""
        system_prompt = """You are helping a job applicant answer application questions.
Provide concise, honest, and professional answers based on the resume.
If the resume doesn't contain relevant info, provide a reasonable professional answer."""

        questions_text = "\n".join(
            f"{i+1}. {q['question']}" for i, q in enumerate(questions)
        )

        prompt = f"""Based on the following resume and job description, answer these application questions:

Resume:
{resume_text[:2000]}

Job Description:
{job_description[:2000]}

Questions:
{questions_text}

Provide answers in the format:
1. [answer]
2. [answer]
...

Keep answers concise (1-3 sentences each) unless the question requires a longer response."""

        response = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.5,
        )

        # Parse responses
        answers = []
        lines = response.strip().split("\n")
        current_answer = ""
        current_idx = 0

        for line in lines:
            stripped = line.strip()
            if stripped and stripped[0].isdigit() and "." in stripped[:3]:
                if current_answer and current_idx > 0:
                    answers.append({
                        "question": questions[current_idx - 1]["question"],
                        "answer": current_answer.strip(),
                    })
                current_idx += 1
                current_answer = stripped.split(".", 1)[1].strip() if "." in stripped else stripped
            else:
                current_answer += " " + stripped

        if current_answer and current_idx > 0 and current_idx <= len(questions):
            answers.append({
                "question": questions[current_idx - 1]["question"],
                "answer": current_answer.strip(),
            })

        return answers

    async def analyze_job_match(
        self,
        job_description: str,
        resume_text: str,
    ) -> dict:
        """Analyze how well a resume matches a job description."""
        system_prompt = """You are a recruitment expert analyzing job fit.
Provide honest, actionable analysis. Return structured JSON."""

        prompt = f"""Analyze the match between this resume and job description.

Job Description:
{job_description[:2500]}

Resume:
{resume_text[:2500]}

Return a JSON object with:
- "match_score": number from 0-100
- "strengths": list of 3-5 matching qualifications
- "gaps": list of missing or weak areas
- "recommendations": list of 2-3 suggestions to improve the application

Return ONLY the JSON object, no other text."""

        response = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.3,
        )

        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("\n", 1)[1]
                clean_response = clean_response.rsplit("```", 1)[0]
            return json.loads(clean_response)
        except json.JSONDecodeError:
            return {
                "match_score": 50,
                "strengths": ["Unable to parse detailed analysis"],
                "gaps": [],
                "recommendations": ["Please try again"],
            }

    async def improve_resume_section(
        self,
        section: str,
        content: str,
        target_role: Optional[str] = None,
    ) -> str:
        """Improve a resume section."""
        system_prompt = """You are an expert resume writer.
Improve resume sections to be more impactful, quantified, and ATS-friendly.
Keep the same truthful information but present it better."""

        prompt = f"""Improve this resume {section} section:

{content}
"""
        if target_role:
            prompt += f"\nTailor it for: {target_role}"

        prompt += "\n\nReturn only the improved section text, ready to paste into a resume."

        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.6,
        )
