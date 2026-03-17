"""
Naukri.com application automation.

Handles one-click apply and questionnaire-based applications
on the Naukri platform.
"""

import asyncio
import logging
import random
from typing import Dict, List, Any, Optional

from worker.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NaukriApplicator(BaseScraper):
    """Naukri.com job application automation."""

    PLATFORM = "naukri"
    BASE_URL = "https://www.naukri.com"
    MIN_DELAY = 1.5
    MAX_DELAY = 3.5

    async def login(self, email: str, password: str) -> bool:
        """Login to Naukri (delegates to NaukriScraper login)."""
        from worker.scrapers.naukri_scraper import NaukriScraper

        scraper = NaukriScraper(user_id=self.user_id)
        scraper.context = self.context
        scraper.page = self.page
        scraper.session_manager = self.session_manager
        result = await scraper.login(email, password)
        self._is_logged_in = result
        return result

    async def search_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """Not used for applicator."""
        raise NotImplementedError("Use NaukriScraper for job search")

    async def apply_to_job(
        self,
        job_url: str,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply to a Naukri job.
        Handles both one-click apply and questionnaire-based applications.

        Args:
            job_url: URL of the Naukri job posting
            user_profile: User profile data
            job_details: Job details for context

        Returns:
            Dict with success status and details
        """
        if not self._is_logged_in:
            return {"success": False, "error": "Not logged in to Naukri"}

        logger.info(f"Applying to Naukri job: {job_url}")
        screenshots = []

        try:
            # Navigate to job page
            await self.page.goto(job_url, wait_until="networkidle")
            await self.random_delay(2.0, 4.0)

            # Take initial screenshot
            initial_ss = await self.take_screenshot("naukri_apply_start")
            if initial_ss:
                screenshots.append(initial_ss)

            # Check for CAPTCHA
            if await self.check_for_captcha():
                return {
                    "success": False,
                    "error": "CAPTCHA detected",
                    "screenshot_url": initial_ss,
                }

            # Check if already applied
            if await self._check_already_applied():
                return {
                    "success": False,
                    "error": "Already applied to this job",
                    "screenshot_url": initial_ss,
                }

            # Find apply button
            apply_button = await self._find_apply_button()
            if not apply_button:
                return {
                    "success": False,
                    "error": "Apply button not found",
                    "screenshot_url": initial_ss,
                }

            # Click apply
            await apply_button.click()
            await self.random_delay(2.0, 4.0)

            # Check for questionnaire/form
            has_questionnaire = await self._check_questionnaire()
            if has_questionnaire:
                result = await self._handle_questionnaire(user_profile, job_details, screenshots)
            else:
                # One-click apply - check for success
                result = await self._check_apply_success()

            # Final screenshot
            final_ss = await self.take_screenshot("naukri_apply_result")
            if final_ss:
                screenshots.append(final_ss)

            result["screenshot_url"] = final_ss or (screenshots[0] if screenshots else "")
            result["screenshots"] = screenshots
            result["method"] = "naukri_apply"
            return result

        except Exception as e:
            logger.error(f"Naukri apply error: {e}", exc_info=True)
            error_ss = await self.take_screenshot("naukri_apply_error")
            return {
                "success": False,
                "error": str(e),
                "screenshot_url": error_ss,
                "screenshots": screenshots,
            }

    async def _find_apply_button(self):
        """Find the apply button on the job page."""
        button_selectors = [
            'button#apply-button',
            'button.apply-button',
            'button[class*="apply"]',
            'a[class*="apply-button"]',
            'button:has-text("Apply")',
            'button:has-text("Apply on company site")',
            '.apply-btn',
            '#applyButton',
        ]

        for selector in button_selectors:
            try:
                button = await self.page.query_selector(selector)
                if button and await button.is_visible():
                    # Verify it's not a "save" or "follow" button
                    text = (await button.text_content() or "").lower()
                    if "apply" in text:
                        return button
            except Exception:
                continue

        return None

    async def _check_already_applied(self) -> bool:
        """Check if user has already applied to this job."""
        already_applied_selectors = [
            'button:has-text("Already Applied")',
            '[class*="already-applied"]',
            '.applied-tag',
            'span:has-text("Already Applied")',
        ]

        for selector in already_applied_selectors:
            if await self.is_element_visible(selector):
                return True
        return False

    async def _check_questionnaire(self) -> bool:
        """Check if a questionnaire/form appeared after clicking apply."""
        questionnaire_selectors = [
            ".apply-questionnaire",
            ".chatbot-container",
            '[class*="questionnaire"]',
            ".apply-dialog",
            'form[class*="apply"]',
            ".apply-modal",
        ]

        for selector in questionnaire_selectors:
            if await self.is_element_visible(selector):
                return True
        return False

    async def _handle_questionnaire(
        self,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
        screenshots: List[str],
    ) -> Dict[str, Any]:
        """Handle Naukri's application questionnaire."""
        from worker.ai.question_answerer import QuestionAnswerer

        logger.info("Handling Naukri questionnaire")
        answerer = QuestionAnswerer()
        max_questions = 15
        answered = 0

        for _ in range(max_questions):
            await self.random_delay(1.0, 2.0)

            # Check if questionnaire is complete
            if await self._check_apply_success_indicator():
                return {"success": True, "questions_answered": answered}

            # Find current question
            question_text = await self._get_current_question()
            if not question_text:
                # Try to find submit button
                submitted = await self._submit_questionnaire()
                if submitted:
                    await self.random_delay(2.0, 3.0)
                    return await self._check_apply_success()
                break

            # Determine input type and get answer
            input_type, options = await self._get_question_input_type()

            answer = await answerer.answer_question(
                question=question_text,
                user_profile=user_profile,
                job_details=job_details,
                answer_type=input_type,
                options=options,
            )

            if answer:
                await self._fill_question_answer(input_type, answer, options)
                answered += 1

            # Take screenshot
            q_ss = await self.take_screenshot(f"naukri_question_{answered}")
            if q_ss:
                screenshots.append(q_ss)

            # Try to go to next question
            next_clicked = await self._click_next_question()
            if not next_clicked:
                submitted = await self._submit_questionnaire()
                if submitted:
                    await self.random_delay(2.0, 3.0)
                    return await self._check_apply_success()
                break

        return {"success": False, "error": "Questionnaire incomplete", "questions_answered": answered}

    async def _get_current_question(self) -> Optional[str]:
        """Get the current question text."""
        question_selectors = [
            ".chatbot-question",
            ".question-text",
            '[class*="question"] label',
            ".apply-questionnaire .question",
            "label.question",
            ".ques-text",
        ]

        for selector in question_selectors:
            el = await self.page.query_selector(selector)
            if el and await el.is_visible():
                text = (await el.text_content() or "").strip()
                if text and len(text) > 3:
                    return text

        return None

    async def _get_question_input_type(self) -> tuple:
        """Determine the input type and options for the current question."""
        # Check for radio buttons
        radios = await self.page.query_selector_all(
            '.chatbot-option, input[type="radio"]:visible, '
            '[class*="option"]:visible'
        )
        if radios:
            options = []
            for radio in radios:
                text = (await radio.text_content() or "").strip()
                if not text:
                    label = await radio.query_selector("label, span")
                    if label:
                        text = (await label.text_content() or "").strip()
                if text:
                    options.append(text)
            if options:
                return "radio", options

        # Check for select dropdown
        select = await self.page.query_selector("select:visible")
        if select:
            option_els = await select.query_selector_all("option")
            options = []
            for opt in option_els:
                text = (await opt.text_content() or "").strip()
                value = await opt.get_attribute("value")
                if text and value:
                    options.append(text)
            return "select", options

        # Check for text input
        text_input = await self.page.query_selector(
            'input[type="text"]:visible, input[type="number"]:visible, '
            "textarea:visible"
        )
        if text_input:
            return "text", []

        return "text", []

    async def _fill_question_answer(
        self, input_type: str, answer: str, options: List[str]
    ):
        """Fill in the answer for the current question."""
        try:
            if input_type == "radio":
                # Click the matching option
                option_elements = await self.page.query_selector_all(
                    '.chatbot-option, [class*="option"], '
                    'input[type="radio"] + label'
                )
                for opt_el in option_elements:
                    text = (await opt_el.text_content() or "").strip()
                    if text.lower() == answer.lower() or answer.lower() in text.lower():
                        await opt_el.click()
                        await self.random_delay(0.3, 0.6)
                        break

            elif input_type == "select":
                select = await self.page.query_selector("select:visible")
                if select:
                    await select.select_option(label=answer)
                    await self.random_delay(0.3, 0.5)

            elif input_type == "text":
                input_el = await self.page.query_selector(
                    'input[type="text"]:visible, input[type="number"]:visible, '
                    "textarea:visible"
                )
                if input_el:
                    await input_el.click()
                    await input_el.fill(str(answer))
                    await self.random_delay(0.3, 0.6)

        except Exception as e:
            logger.warning(f"Failed to fill answer: {e}")

    async def _click_next_question(self) -> bool:
        """Click next/continue button in questionnaire."""
        next_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button[class*="next"]',
            ".chatbot-send-btn",
            'button:has-text("Save")',
        ]

        for selector in next_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    await self.random_delay(1.0, 2.0)
                    return True
            except Exception:
                continue

        return False

    async def _submit_questionnaire(self) -> bool:
        """Submit the questionnaire."""
        submit_selectors = [
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button[type="submit"]',
            'button:has-text("Done")',
            ".submit-btn",
        ]

        for selector in submit_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    await self.random_delay(2.0, 3.0)
                    return True
            except Exception:
                continue

        return False

    async def _check_apply_success(self) -> Dict[str, Any]:
        """Check if application was successful."""
        if await self._check_apply_success_indicator():
            return {"success": True}
        return {"success": False, "error": "Application success not confirmed"}

    async def _check_apply_success_indicator(self) -> bool:
        """Check for success indicators after applying."""
        success_selectors = [
            '[class*="success"]',
            ':has-text("successfully applied")',
            ':has-text("application submitted")',
            ':has-text("applied successfully")',
            ".apply-success",
            ".congratulations",
        ]

        for selector in success_selectors:
            try:
                if await self.is_element_visible(selector):
                    return True
            except Exception:
                continue

        # Check page text
        try:
            body_text = await self.get_page_text()
            success_phrases = [
                "successfully applied",
                "application submitted",
                "applied successfully",
                "congratulations",
            ]
            for phrase in success_phrases:
                if phrase in body_text.lower():
                    return True
        except Exception:
            pass

        return False
