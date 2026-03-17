"""
AI-powered email response classification.

Classifies incoming email responses into categories:
interested, not_interested, question, out_of_office, or other.
"""

import logging
import os
import json
from typing import Dict, Any

import anthropic

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


class ResponseClassifier:
    """Classifies email responses using AI."""

    CATEGORIES = [
        "interested",       # Positive response, wants to proceed
        "not_interested",   # Rejection or no current openings
        "question",         # Asks for more info (salary, experience, etc.)
        "out_of_office",    # Auto-reply, OOO
        "other",            # Anything else
    ]

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ANTHROPIC_MODEL

    async def classify(
        self,
        original_subject: str,
        original_body: str,
        response_subject: str,
        response_body: str,
        company: str = "",
        role: str = "",
    ) -> Dict[str, Any]:
        """
        Classify an email response.

        Args:
            original_subject: Subject of the original cold email
            original_body: Body of the original cold email
            response_subject: Subject of the response
            response_body: Body of the response
            company: Company name for context
            role: Job role for context

        Returns:
            Dict with 'category', 'confidence', 'summary', and 'action' keys
        """
        # First try rule-based classification for obvious cases
        rule_result = self._rule_based_classify(response_subject, response_body)
        if rule_result and rule_result["confidence"] >= 0.95:
            return rule_result

        # Use AI for nuanced classification
        try:
            return await self._ai_classify(
                original_subject, original_body,
                response_subject, response_body,
                company, role,
            )
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            # Fall back to rule-based if available
            if rule_result:
                return rule_result
            return {
                "category": "other",
                "confidence": 0.3,
                "summary": "Classification failed",
                "action": "manual_review",
            }

    def _rule_based_classify(
        self, subject: str, body: str
    ) -> Dict[str, Any]:
        """Rule-based classification for obvious cases."""
        subject_lower = (subject or "").lower()
        body_lower = (body or "").lower()
        combined = f"{subject_lower} {body_lower}"

        # Out of office detection
        ooo_patterns = [
            "out of office", "on vacation", "on leave", "automatic reply",
            "auto-reply", "autoreply", "i am currently out",
            "away from the office", "limited access to email",
            "will be back on", "returning on", "ooo",
        ]
        if any(pattern in combined for pattern in ooo_patterns):
            return {
                "category": "out_of_office",
                "confidence": 0.98,
                "summary": "Automated out-of-office reply",
                "action": "wait_and_retry",
            }

        # Clear rejection
        rejection_patterns = [
            "not hiring", "no openings", "position has been filled",
            "we have decided to move forward with", "unfortunately",
            "not a fit", "not a match", "we will not be moving forward",
            "we regret to inform", "we have chosen another candidate",
            "not interested at this time", "no longer available",
        ]
        if any(pattern in combined for pattern in rejection_patterns):
            return {
                "category": "not_interested",
                "confidence": 0.90,
                "summary": "Rejection or no current openings",
                "action": "close",
            }

        # Clear interest
        interest_patterns = [
            "would love to chat", "let's schedule", "can we set up a call",
            "please share your availability", "interested in learning more",
            "looks great", "impressive background", "let's connect",
            "when are you available", "would you be free for",
            "i'd like to schedule", "please send your resume",
            "can you come in for", "next steps",
        ]
        if any(pattern in combined for pattern in interest_patterns):
            return {
                "category": "interested",
                "confidence": 0.90,
                "summary": "Positive response, wants to proceed",
                "action": "respond_quickly",
            }

        # Question detection
        question_patterns = [
            "what is your", "can you share", "could you provide",
            "what are your salary", "notice period",
            "how many years", "do you have experience",
            "are you open to", "would you be willing",
        ]
        if any(pattern in combined for pattern in question_patterns):
            return {
                "category": "question",
                "confidence": 0.85,
                "summary": "Recruiter asking for more information",
                "action": "respond_with_info",
            }

        return None

    async def _ai_classify(
        self,
        original_subject: str,
        original_body: str,
        response_subject: str,
        response_body: str,
        company: str,
        role: str,
    ) -> Dict[str, Any]:
        """Use AI to classify the email response."""
        prompt = f"""Classify this email response to a job application cold email.

ORIGINAL EMAIL (sent by the candidate):
Subject: {original_subject}
Body: {original_body[:300]}

RESPONSE RECEIVED:
Subject: {response_subject}
Body: {response_body[:1000]}

Context: Application for {role} at {company}

CLASSIFY into one of these categories:
- "interested": Positive response, wants to schedule call/interview, asks for resume/availability
- "not_interested": Rejection, no openings, position filled, not a fit
- "question": Asks for more info (salary expectations, experience details, availability)
- "out_of_office": Auto-reply, vacation, OOO message
- "other": Unrelated, spam, or unclear

Respond with JSON:
{{
    "category": "one of the categories above",
    "confidence": 0.0 to 1.0,
    "summary": "brief 1-sentence summary of the response",
    "action": "recommended action (respond_quickly/respond_with_info/wait_and_retry/close/manual_review)",
    "key_info": "any extracted key information (meeting time, salary question, etc.)"
}}

Respond ONLY with the JSON object."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        response_text = response.content[0].text.strip()

        # Parse JSON
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]

        result = json.loads(response_text)

        # Validate category
        if result.get("category") not in self.CATEGORIES:
            result["category"] = "other"

        # Ensure confidence is a float
        result["confidence"] = float(result.get("confidence", 0.5))

        logger.info(
            f"Email classified as '{result['category']}' "
            f"(confidence: {result['confidence']:.2f})"
        )
        return result

    async def classify_batch(
        self,
        emails: list,
    ) -> list:
        """Classify a batch of email responses."""
        results = []
        for email in emails:
            result = await self.classify(
                original_subject=email.get("original_subject", ""),
                original_body=email.get("original_body", ""),
                response_subject=email.get("response_subject", ""),
                response_body=email.get("response_body", ""),
                company=email.get("company", ""),
                role=email.get("role", ""),
            )
            results.append(result)
        return results
