"""
AI-powered job matching and scoring.

Scores jobs on a 0-100 scale based on user profile, skills,
preferences, and job requirements using LLM (Gemini/Claude).
"""

import logging
import os
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class JobMatcher:
    """AI-powered job matching and scoring engine."""

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
                logger.info("JobMatcher using Gemini")
            except ImportError:
                logger.error("google-generativeai not installed")
                raise
        else:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
            self.provider = "anthropic"
            logger.info("JobMatcher using Anthropic")

    async def score_jobs(
        self,
        user_profile: Dict[str, Any],
        jobs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Score a batch of jobs against a user profile.

        Args:
            user_profile: User's profile with skills, experience, preferences
            jobs: List of job dictionaries to score

        Returns:
            List of dicts with 'score' (0-100) and 'reasoning' keys
        """
        if not jobs:
            return []

        try:
            # Build profile context
            profile_context = self._build_profile_context(user_profile)

            # Build jobs context
            jobs_context = self._build_jobs_context(jobs)

            prompt = f"""You are a professional job-candidate matching engine. Evaluate each job against the candidate profile and return structured scores.

CANDIDATE PROFILE:
{profile_context}

JOBS TO SCORE:
{jobs_context}

SCORING RUBRIC (component weights, overall_score = sum of components):
- skills_score (0-35): Overlap between candidate skills and job requirements. 35 = perfect match, 0 = no overlap.
- experience_score (0-25): How well candidate experience aligns with job requirements. 25 = ideal fit, 0 = severe mismatch.
- role_score (0-20): Alignment between candidate target roles and job title/responsibilities. 20 = exact match, 0 = unrelated role.
- location_score (0-10): Match between candidate location preferences and job location/remote policy. 10 = perfect, 0 = incompatible.
- salary_score (0-10): Compatibility of salary expectations with job compensation. 10 = within range, 0 = far outside range. If salary info unavailable, default to 5.

HARD CAP RULE: If the experience gap between candidate and job requirement exceeds 2 years in EITHER direction (candidate too junior OR too senior), overall_score MUST NOT exceed 40 regardless of component sums.

For each job return a JSON object with:
- job_index: integer (0-based)
- overall_score: integer 0-100 (must equal sum of components, subject to hard cap)
- skills_score, experience_score, role_score, location_score, salary_score: integers per rubric
- reasoning: 1-2 sentence explanation
- strengths: array of candidate strengths for this role (1-3 items)
- gaps: array of candidate gaps/weaknesses for this role (1-3 items)
- matched_skills: array of candidate skills that match job requirements
- missing_skills: array of job-required skills the candidate lacks

Respond with a JSON array only, no markdown or code blocks:
[
  {{"job_index": 0, "overall_score": 72, "skills_score": 28, "experience_score": 20, "role_score": 14, "location_score": 5, "salary_score": 5, "reasoning": "Strong Python/FastAPI overlap but missing Kubernetes experience.", "strengths": ["Python expertise", "Relevant backend experience"], "gaps": ["No Kubernetes experience"], "matched_skills": ["Python", "FastAPI", "PostgreSQL"], "missing_skills": ["Kubernetes", "Terraform"]}},
  ...
]"""

            if self.provider == "gemini":
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config={"temperature": 0.3, "max_output_tokens": 16384},
                )
                response_text = response.text.strip()
                # Check if response was truncated
                if response.candidates and response.candidates[0].finish_reason != 1:
                    logger.warning(f"Gemini response truncated (finish_reason={response.candidates[0].finish_reason}), response length: {len(response_text)}")
            else:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                response_text = response.content[0].text.strip()

            # Parse JSON response — clean up common LLM formatting issues
            logger.debug(f"Raw LLM response ({len(response_text)} chars): {response_text[:500]}")
            scores = self._parse_llm_json(response_text)

            # Ensure we have scores for all jobs
            result = []
            for i in range(len(jobs)):
                score_data = next(
                    (s for s in scores if s.get("job_index") == i),
                    {"overall_score": 50, "reasoning": "Unable to score - default applied"}
                )
                result.append({
                    "score": max(0, min(100, int(score_data.get("overall_score", score_data.get("score", 50))))),
                    "skills_score": int(score_data.get("skills_score", 0)),
                    "experience_score": int(score_data.get("experience_score", 0)),
                    "role_score": int(score_data.get("role_score", 0)),
                    "location_score": int(score_data.get("location_score", 0)),
                    "salary_score": int(score_data.get("salary_score", 0)),
                    "reasoning": score_data.get("reasoning", ""),
                    "strengths": score_data.get("strengths", []),
                    "gaps": score_data.get("gaps", []),
                    "matched_skills": score_data.get("matched_skills", []),
                    "missing_skills": score_data.get("missing_skills", []),
                })

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI scoring response: {e}")
            return self._fallback_scoring(user_profile, jobs)
        except Exception as e:
            logger.error(f"Job matching failed: {e}", exc_info=True)
            return self._fallback_scoring(user_profile, jobs)

    @staticmethod
    def _parse_llm_json(text: str) -> list:
        """Parse JSON from LLM response, handling common formatting issues."""
        import re

        # Strip markdown code fences
        if "```" in text:
            # Remove ```json ... ``` or ``` ... ```
            text = re.sub(r'```(?:json)?\s*', '', text)
            text = text.replace('```', '')
        text = text.strip()

        # Extract the JSON array from surrounding text
        bracket_start = text.find('[')
        bracket_end = text.rfind(']')
        if bracket_start != -1 and bracket_end != -1:
            text = text[bracket_start:bracket_end + 1]

        # Fix common LLM JSON issues
        # 1. Trailing commas before } or ]
        text = re.sub(r',\s*([}\]])', r'\1', text)
        # 2. Single quotes instead of double quotes (but not inside strings)
        # 3. Unescaped newlines inside string values
        text = re.sub(r'(?<!\\)\n\s*(?=[^"]*"[,}\]])', ' ', text)
        # 4. Comments (// style)
        text = re.sub(r'//[^\n]*', '', text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Last resort: try to extract individual JSON objects and build array
        try:
            objects = []
            for match in re.finditer(r'\{[^{}]*\}', text):
                try:
                    obj = json.loads(match.group())
                    if "job_index" in obj or "overall_score" in obj or "score" in obj:
                        objects.append(obj)
                except json.JSONDecodeError:
                    continue
            if objects:
                return objects
        except Exception:
            pass

        raise json.JSONDecodeError("Could not parse LLM response as JSON", text, 0)

    async def score_single_job(
        self,
        user_profile: Dict[str, Any],
        job: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Score a single job against a user profile."""
        results = await self.score_jobs(user_profile, [job])
        return results[0] if results else {"score": 50, "reasoning": "Scoring failed"}

    def _build_profile_context(self, profile: Dict[str, Any]) -> str:
        """Build profile context for the scoring prompt."""
        parts = []

        if profile.get("full_name"):
            parts.append(f"Name: {profile['full_name']}")
        if profile.get("current_title"):
            parts.append(f"Current Role: {profile['current_title']}")
        if profile.get("experience_years"):
            parts.append(f"Experience: {profile['experience_years']} years")

        # Target roles
        target_roles = profile.get("target_roles", [])
        if isinstance(target_roles, str):
            target_roles = [r.strip() for r in target_roles.split(",")]
        if target_roles:
            parts.append(f"Target Roles: {', '.join(target_roles)}")

        # Skills
        skills = profile.get("skills", "")
        if isinstance(skills, list):
            skills = ", ".join(skills)
        if skills:
            parts.append(f"Skills: {skills}")

        # Location preferences
        locations = profile.get("target_locations", [])
        if isinstance(locations, str):
            locations = [l.strip() for l in locations.split(",")]
        if locations:
            parts.append(f"Preferred Locations: {', '.join(locations)}")

        # Remote preference
        remote_pref = profile.get("remote_preference", "any")
        parts.append(f"Remote Preference: {remote_pref}")

        # Salary expectations
        min_salary = profile.get("min_salary")
        max_salary = profile.get("max_salary")
        if min_salary or max_salary:
            salary_str = f"{min_salary or 'any'} - {max_salary or 'any'}"
            parts.append(f"Salary Range: {salary_str}")

        # Job type preferences
        job_types = profile.get("preferred_job_types", [])
        if isinstance(job_types, str):
            job_types = [j.strip() for j in job_types.split(",")]
        if job_types:
            parts.append(f"Job Types: {', '.join(job_types)}")

        # Education
        education = profile.get("education") or profile.get("highest_degree")
        if education:
            parts.append(f"Education: {education}")

        # Resume summary
        if profile.get("bio"):
            parts.append(f"Summary: {profile['bio'][:300]}")

        return "\n".join(parts)

    def _build_jobs_context(self, jobs: List[Dict[str, Any]]) -> str:
        """Build jobs context for the scoring prompt."""
        job_descriptions = []

        for i, job in enumerate(jobs):
            parts = [f"\n--- Job {i} ---"]
            if job.get("title"):
                parts.append(f"Title: {job['title']}")
            if job.get("company"):
                parts.append(f"Company: {job['company']}")
            if job.get("location"):
                parts.append(f"Location: {job['location']}")
            if job.get("job_type"):
                parts.append(f"Type: {job['job_type']}")
            if job.get("salary_min") or job.get("salary_max"):
                parts.append(f"Salary: {job.get('salary_min', 'N/A')} - {job.get('salary_max', 'N/A')}")
            required_skills = job.get("required_skills")
            if required_skills:
                if isinstance(required_skills, list):
                    required_skills = ", ".join(required_skills)
                parts.append(f"Required Skills: {required_skills}")
            if job.get("is_easy_apply"):
                parts.append("Easy Apply: Yes")
            if job.get("description"):
                # Limit description to avoid token limits
                desc = job["description"][:1000]
                parts.append(f"Description: {desc}")

            job_descriptions.append("\n".join(parts))

        return "\n".join(job_descriptions)

    def _fallback_scoring(
        self,
        user_profile: Dict[str, Any],
        jobs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rule-based fallback scoring when AI is unavailable."""
        user_skills = set()
        skills_str = user_profile.get("skills", "")
        if isinstance(skills_str, list):
            user_skills = set(s.lower() for s in skills_str)
        elif isinstance(skills_str, str):
            user_skills = set(s.strip().lower() for s in skills_str.split(",") if s.strip())

        target_roles = user_profile.get("target_roles", [])
        if isinstance(target_roles, str):
            target_roles = [r.strip().lower() for r in target_roles.split(",")]
        else:
            target_roles = [r.lower() for r in target_roles]

        target_locations = user_profile.get("target_locations", [])
        if isinstance(target_locations, str):
            target_locations = [l.strip().lower() for l in target_locations.split(",")]
        else:
            target_locations = [l.lower() for l in target_locations]

        results = []
        for job in jobs:
            # Skills matching (0-35)
            job_skills = set()
            raw_skills = job.get("required_skills") or job.get("skills", "")
            if isinstance(raw_skills, list):
                job_skills = set(s.lower() for s in raw_skills)
            elif isinstance(raw_skills, str):
                job_skills = set(s.strip().lower() for s in raw_skills.split(",") if s.strip())

            matched = user_skills & job_skills
            skills_score = int((len(matched) / max(len(job_skills), 1)) * 35) if user_skills and job_skills else 0

            # Role title matching (0-20)
            role_score = 0
            job_title = (job.get("title", "") or "").lower()
            for role in target_roles:
                if role in job_title or job_title in role:
                    role_score = 20
                    break
                role_words = set(role.split())
                title_words = set(job_title.split())
                if role_words & title_words:
                    role_score = 10
                    break

            # Experience (0-25) — simple heuristic
            experience_score = 15  # default mid-range

            # Location matching (0-10)
            location_score = 0
            job_location = (job.get("location", "") or "").lower()
            for loc in target_locations:
                if loc in job_location:
                    location_score = 10
                    break

            # Salary (0-10) — default mid when unknown
            salary_score = 5

            score = min(100, skills_score + experience_score + role_score + location_score + salary_score)

            missing = list(job_skills - user_skills) if job_skills else []
            reasoning = f"Fallback scoring: skills={len(matched)}/{len(job_skills)} match"
            results.append({
                "score": score,
                "skills_score": skills_score,
                "experience_score": experience_score,
                "role_score": role_score,
                "location_score": location_score,
                "salary_score": salary_score,
                "reasoning": reasoning,
                "strengths": [],
                "gaps": [],
                "matched_skills": list(matched),
                "missing_skills": missing,
            })

        return results
