"""
LinkedIn Easy Apply automation.

Handles multi-step application forms, resume upload, cover letter,
AI-powered screening question answering, and screenshot capture.
"""

import asyncio
import logging
import random
import re
from typing import Dict, List, Any, Optional

from worker.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Modal selectors (LinkedIn updates these periodically)
MODAL_SELECTORS = [
    '.jobs-easy-apply-modal',
    '[class*="easy-apply-modal"]',
    '.artdeco-modal:has(.jobs-easy-apply-content)',
    '.artdeco-modal',
]

# Form section container selectors
FORM_SECTION_SELECTORS = (
    ".jobs-easy-apply-form-section__grouping, "
    "[class*='form-component'], "
    ".fb-dash-form-element"
)


class LinkedInApplicator(BaseScraper):
    """LinkedIn Easy Apply automation with intelligent form filling."""

    PLATFORM = "linkedin"
    BASE_URL = "https://www.linkedin.com"
    MIN_DELAY = 1.5
    MAX_DELAY = 4.0

    def __init__(self, user_id: str):
        super().__init__(user_id)
        self._modal = None  # Cache the modal element

    async def login(self, email: str, password: str) -> bool:
        """Login to LinkedIn (delegates to LinkedInScraper login logic)."""
        from worker.scrapers.linkedin_scraper import LinkedInScraper

        scraper = LinkedInScraper(user_id=self.user_id)
        scraper.context = self.context
        scraper.page = self.page
        scraper.session_manager = self.session_manager
        result = await scraper.login(email, password)
        self._is_logged_in = result
        return result

    async def search_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """Not used for applicator - delegates to scraper."""
        raise NotImplementedError("Use LinkedInScraper for job search")

    async def apply_to_job(
        self,
        job_url: str,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply to a LinkedIn job using Easy Apply.

        Args:
            job_url: URL of the job posting
            user_profile: User's profile data for form filling
            job_details: Job details for context

        Returns:
            Dict with success status, screenshot URL, and any errors
        """
        if not self._is_logged_in:
            return {"success": False, "error": "Not logged in"}

        logger.info(f"Applying to LinkedIn job: {job_url}")
        screenshots = []

        try:
            # Navigate to job page
            await self.page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
            await self.random_delay(2.0, 4.0)

            # Wait for the job page to fully render (apply button area)
            try:
                await self.page.wait_for_selector(
                    '.jobs-unified-top-card, .job-details-jobs-unified-top-card__content--two-pane, '
                    '.jobs-details__main-content, .scaffold-layout__detail',
                    timeout=10000,
                )
            except Exception:
                logger.debug("Top card container not found, continuing anyway")

            # Take initial screenshot
            initial_ss = await self.take_screenshot("linkedin_apply_start")
            if initial_ss:
                screenshots.append(initial_ss)

            # Check for CAPTCHA
            if await self.check_for_captcha():
                return {
                    "success": False,
                    "error": "CAPTCHA detected",
                    "screenshot_url": initial_ss,
                }

            # Check if job is no longer accepting applications
            if await self._check_job_expired():
                logger.info(f"Job no longer accepting applications: {job_url}")
                return {
                    "success": False,
                    "error": "Job expired - no longer accepting applications",
                    "expired": True,
                    "screenshot_url": initial_ss,
                }

            # Check if already applied
            if await self._check_already_applied():
                logger.info(f"Already applied to job: {job_url}")
                return {
                    "success": False,
                    "error": "Already applied to this job",
                    "already_applied": True,
                    "screenshot_url": initial_ss,
                }

            # Find and click Easy Apply button
            apply_button = await self._find_easy_apply_button()
            if not apply_button:
                if getattr(self, '_is_external_apply', False):
                    return {
                        "success": False,
                        "error": "External apply only - not Easy Apply",
                        "external_apply": True,
                        "screenshot_url": initial_ss,
                    }
                return {
                    "success": False,
                    "error": "Easy Apply button not found",
                    "screenshot_url": initial_ss,
                }

            await apply_button.click()
            logger.info("Clicked Easy Apply button, waiting for modal...")

            # Wait for the modal to appear
            modal = await self._wait_for_modal()
            if not modal:
                error_ss = await self.take_screenshot("linkedin_apply_no_modal")
                return {
                    "success": False,
                    "error": "Easy Apply modal did not open",
                    "screenshot_url": error_ss,
                }

            logger.info("Easy Apply modal opened successfully")
            await self.random_delay(1.0, 2.0)

            # Handle multi-step application form
            result = await self._process_application_form(user_profile, job_details, screenshots)

            # Take final screenshot
            final_ss = await self.take_screenshot("linkedin_apply_result")
            if final_ss:
                screenshots.append(final_ss)

            result["screenshot_url"] = final_ss or (screenshots[0] if screenshots else "")
            result["screenshots"] = screenshots
            return result

        except Exception as e:
            logger.error(f"LinkedIn apply error: {e}", exc_info=True)
            error_ss = await self.take_screenshot("linkedin_apply_error")
            return {
                "success": False,
                "error": str(e),
                "screenshot_url": error_ss,
                "screenshots": screenshots,
            }

    # ── Pre-apply checks ──────────────────────────────────────────────

    async def _find_easy_apply_button(self):
        """Find the Easy Apply button on the job page.

        Returns:
            - The button element if Easy Apply is available
            - None if not found or if it's an external Apply button
        Sets self._is_external_apply = True if the button is external Apply.
        """
        self._is_external_apply = False

        # First, try to find ANY apply button on the page
        apply_button_selectors = [
            'button.jobs-apply-button[aria-label*="Easy Apply"]',
            'button[aria-label*="Easy Apply"]',
            'button:has-text("Easy Apply")',
            '.jobs-s-apply button',
            'button[class*="jobs-apply-button"]',
            '.jobs-apply-button--top-card button',
        ]

        # Try each selector with a short timeout
        for selector in apply_button_selectors:
            try:
                button = await self.page.wait_for_selector(selector, timeout=3000)
                if button and await button.is_visible():
                    # Verify it's actually Easy Apply, not external Apply
                    btn_text = (await button.text_content() or "").strip().lower()
                    aria_label = (await button.get_attribute("aria-label") or "").lower()

                    if "easy apply" in btn_text or "easy apply" in aria_label:
                        logger.info(f"Found Easy Apply button with selector: {selector}")
                        return button
                    else:
                        # This is an external Apply button
                        logger.info(f"Found external Apply button (not Easy Apply): text='{btn_text}', aria='{aria_label}'")
                        self._is_external_apply = True
                        return None
            except Exception:
                continue

        # Fallback: Use JavaScript to search for any apply-like button
        try:
            button = await self.page.evaluate_handle("""
                () => {
                    // Search all buttons for "Easy Apply" text
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        const text = btn.textContent.trim().toLowerCase();
                        if (text.includes('easy apply')) {
                            return btn;
                        }
                    }
                    // Check for any apply button to distinguish external
                    for (const btn of buttons) {
                        const text = btn.textContent.trim().toLowerCase();
                        if (text === 'apply' || (text.includes('apply') && !text.includes('easy'))) {
                            return btn;
                        }
                    }
                    return null;
                }
            """)
            if button:
                element = button.as_element()
                if element:
                    btn_text = (await element.text_content() or "").strip().lower()
                    if "easy apply" in btn_text:
                        logger.info("Found Easy Apply button via JS fallback")
                        return element
                    else:
                        logger.info(f"Found external Apply button via JS: '{btn_text}'")
                        self._is_external_apply = True
                        return None
        except Exception as e:
            logger.debug(f"JS button search failed: {e}")

        logger.warning("No apply button found on job page at all")
        return None

    async def _check_job_expired(self) -> bool:
        """Check if the job posting is no longer accepting applications."""
        expired_selectors = [
            'text="No longer accepting applications"',
            'text="This job is no longer available"',
            '.artdeco-inline-feedback:has-text("No longer")',
            '.jobs-details-top-card__apply-error',
        ]
        for selector in expired_selectors:
            try:
                el = await self.page.query_selector(selector)
                if el and await el.is_visible():
                    return True
            except Exception:
                continue

        # Also check page text for common expired phrases
        try:
            body_text = await self.get_page_text()
            lower_text = body_text.lower()
            if "no longer accepting applications" in lower_text:
                return True
            if "this job is no longer available" in lower_text:
                return True
        except Exception:
            pass

        return False

    async def _check_already_applied(self) -> bool:
        """Check if already applied to this job."""
        try:
            # Check for "Applied" status badge
            page_text = await self.get_page_text()
            if "you applied on" in page_text.lower():
                return True
            if "application was sent" in page_text.lower():
                return True
        except Exception:
            pass

        try:
            applied_el = await self.page.query_selector(
                '.jobs-details-top-card__apply-status, '
                '.artdeco-inline-feedback:has-text("Applied")'
            )
            if applied_el and await applied_el.is_visible():
                return True
        except Exception:
            pass

        return False

    # ── Modal handling ─────────────────────────────────────────────────

    async def _wait_for_modal(self, timeout: int = 10000) -> Optional[Any]:
        """Wait for the Easy Apply modal to appear after clicking the button."""
        for selector in MODAL_SELECTORS:
            try:
                modal = await self.page.wait_for_selector(
                    selector, state="visible", timeout=timeout
                )
                if modal:
                    self._modal = modal
                    return modal
            except Exception:
                continue

        # Fallback: check if any artdeco modal with form content appeared
        try:
            modal = await self.page.wait_for_selector(
                '.artdeco-modal', state="visible", timeout=3000
            )
            if modal:
                # Verify it has form content (not just any modal)
                has_form = await modal.query_selector(
                    'form, input, select, button:has-text("Next"), '
                    'button:has-text("Submit")'
                )
                if has_form:
                    self._modal = modal
                    return modal
        except Exception:
            pass

        self._modal = None
        return None

    async def _get_modal(self):
        """Get the current modal element, refreshing if stale."""
        for selector in MODAL_SELECTORS:
            try:
                modal = await self.page.query_selector(selector)
                if modal and await modal.is_visible():
                    self._modal = modal
                    return modal
            except Exception:
                continue

        # Broader fallback
        try:
            modal = await self.page.query_selector('.artdeco-modal')
            if modal and await modal.is_visible():
                self._modal = modal
                return modal
        except Exception:
            pass

        return None

    async def _check_form_dismissed(self) -> bool:
        """Check if the form modal was dismissed/closed."""
        modal = await self._get_modal()
        if modal:
            return False

        # Modal not found - but wait a moment and retry (it might be re-rendering)
        await asyncio.sleep(1.0)
        modal = await self._get_modal()
        if modal:
            return False

        logger.warning("Easy Apply modal appears to be dismissed")
        return True

    async def _get_modal_header(self) -> str:
        """Get the current step header text from the modal (e.g. 'Contact info', 'Resume')."""
        try:
            modal = await self._get_modal()
            if not modal:
                return ""
            header = await modal.query_selector('h3, h2, .t-16.t-bold')
            if header:
                return (await header.text_content() or "").strip()
        except Exception:
            pass
        return ""

    # ── Form processing loop ──────────────────────────────────────────

    async def _process_application_form(
        self,
        user_profile: Dict[str, Any],
        job_details: Dict[str, Any],
        screenshots: List[str],
    ) -> Dict[str, Any]:
        """
        Process the multi-step Easy Apply form.
        Handles contact info, resume, screening questions, and review.
        """
        max_steps = 10  # Safety limit
        step = 0

        while step < max_steps:
            step += 1
            await self.random_delay(1.0, 2.0)

            # Check if application was submitted
            if await self._check_submission_success():
                logger.info("Application submitted successfully!")
                return {"success": True, "method": "easy_apply", "steps_completed": step}

            # Check for error/dismissed modal
            if await self._check_form_dismissed():
                return {"success": False, "error": "Application form was dismissed"}

            # Detect current step
            step_header = await self._get_modal_header()
            logger.info(f"Processing step {step}: '{step_header}'")

            # Take step screenshot
            step_ss = await self.take_screenshot(f"linkedin_apply_step_{step}")
            if step_ss:
                screenshots.append(step_ss)

            # Check for validation errors from previous step
            has_errors = await self._check_validation_errors()
            if has_errors:
                logger.warning(f"Validation errors detected at step {step}")
                # Try AI-powered fallback to fill ALL empty required fields
                await self._fill_unfilled_required_fields(user_profile, job_details)
                # Take screenshot of error state
                err_ss = await self.take_screenshot(f"linkedin_apply_validation_error_{step}")
                if err_ss:
                    screenshots.append(err_ss)

            # Fill the current step
            await self._fill_current_step(user_profile, job_details)

            # Try to advance to next step
            advanced = await self._advance_form()
            if advanced:
                logger.info(f"Advanced past step {step}")
                continue

            # Advance failed - check if we're on the review/submit step
            submitted = await self._try_submit()
            if submitted:
                logger.info("Clicked Submit, checking for success...")
                await self.random_delay(2.0, 4.0)

                if await self._check_submission_success():
                    logger.info("Application submitted successfully!")
                    return {"success": True, "method": "easy_apply", "steps_completed": step}

                # Submit clicked but no success confirmation yet - wait more
                await self.random_delay(2.0, 3.0)
                if await self._check_submission_success():
                    return {"success": True, "method": "easy_apply", "steps_completed": step}

                # Take screenshot to see what happened
                post_submit_ss = await self.take_screenshot("linkedin_apply_post_submit")
                if post_submit_ss:
                    screenshots.append(post_submit_ss)
                return {"success": False, "error": "Submit clicked but success not confirmed"}

            # Neither advance nor submit worked
            logger.warning(f"Cannot advance or submit at step {step}")

            # Last resort: try clicking any primary button in the modal
            fallback = await self._click_primary_button()
            if fallback:
                logger.info("Clicked fallback primary button")
                continue

            return {"success": False, "error": f"Stuck at step {step}: '{step_header}'"}

        return {"success": False, "error": "Max steps reached"}

    # ── Step filling ──────────────────────────────────────────────────

    async def _fill_current_step(
        self, user_profile: Dict[str, Any], job_details: Dict[str, Any]
    ):
        """Detect and fill the current form step."""
        # Handle resume selection/upload
        await self._handle_resume(user_profile)

        # Handle cover letter
        await self._handle_cover_letter(user_profile, job_details)

        # Fill standard form fields (text, select, radio, checkbox)
        await self._fill_text_fields(user_profile)
        await self._fill_select_fields(user_profile)
        await self._fill_radio_fields(user_profile)
        await self._fill_checkbox_fields(user_profile)

        # Handle LinkedIn typeahead/autocomplete dropdowns (city, school, etc.)
        await self._handle_typeahead_fields(user_profile, job_details)

        # Handle screening questions with AI (for fields not covered above)
        await self._handle_screening_questions(user_profile, job_details)

    async def _handle_resume(self, user_profile: Dict[str, Any]):
        """Handle resume - select existing or upload new."""
        # First check if there are already-uploaded resumes to select from
        # LinkedIn shows these as a list with radio buttons or a "selected" state
        resume_selected = await self._select_existing_resume()
        if resume_selected:
            return

        # No existing resume selected - try file upload
        await self._handle_resume_upload(user_profile)

    async def _select_existing_resume(self) -> bool:
        """Select a previously uploaded resume if available."""
        try:
            # LinkedIn shows uploaded resumes in a document list
            # Each resume is in a container with a radio-like selection
            resume_items = await self.page.query_selector_all(
                '.jobs-document-upload-redesign-card__container, '
                '[class*="document-upload"] [class*="card"], '
                '.ui-attachment--pdf'
            )

            if not resume_items:
                return False

            # Check if one is already selected
            for item in resume_items:
                try:
                    is_selected = await item.evaluate(
                        'el => el.classList.contains("jobs-document-upload-redesign-card__container--selected") '
                        '|| el.querySelector("input[type=radio]:checked") !== null '
                        '|| el.getAttribute("aria-checked") === "true"'
                    )
                    if is_selected:
                        logger.info("Resume already selected")
                        return True
                except Exception:
                    continue

            # Select the first available resume
            if resume_items:
                try:
                    await resume_items[0].click()
                    await self.random_delay(0.5, 1.0)
                    logger.info("Selected first available resume")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to click resume item: {e}")

            # Try radio button approach
            resume_radio = await self.page.query_selector(
                '[name*="resume"] input[type="radio"], '
                '[class*="document"] input[type="radio"]'
            )
            if resume_radio:
                await resume_radio.click()
                await self.random_delay(0.5, 1.0)
                logger.info("Selected resume via radio button")
                return True

        except Exception as e:
            logger.debug(f"Resume selection error: {e}")

        return False

    async def _handle_resume_upload(self, user_profile: Dict[str, Any]):
        """Handle resume file upload if present."""
        resume_path = user_profile.get("resume_file_path")
        if not resume_path:
            logger.debug("No resume file path in user profile")
            return

        upload_selectors = [
            'input[type="file"][accept*=".pdf"]',
            'input[type="file"][name*="resume"]',
            'input[type="file"][id*="resume"]',
            'input[type="file"]',
        ]

        for selector in upload_selectors:
            try:
                file_input = await self.page.query_selector(selector)
                if file_input:
                    await file_input.set_input_files(resume_path)
                    logger.info(f"Resume uploaded: {resume_path}")
                    await self.random_delay(1.0, 2.0)
                    return
            except Exception as e:
                logger.debug(f"Resume upload failed with {selector}: {e}")
                continue

    async def _handle_cover_letter(
        self, user_profile: Dict[str, Any], job_details: Dict[str, Any]
    ):
        """Generate and fill cover letter if field is present."""
        cover_letter_selectors = [
            'textarea[name*="cover"]',
            'textarea[id*="cover"]',
            'textarea[aria-label*="cover letter"]',
            'textarea[placeholder*="cover letter"]',
        ]

        for selector in cover_letter_selectors:
            try:
                textarea = await self.page.query_selector(selector)
                if textarea and await textarea.is_visible():
                    # Check if already filled (use input_value for form elements)
                    current = await textarea.input_value() or ""
                    if current.strip():
                        continue

                    from worker.ai.cover_letter_generator import CoverLetterGenerator
                    generator = CoverLetterGenerator()
                    cover_letter = await generator.generate(user_profile, job_details)

                    if cover_letter:
                        await textarea.click()
                        await textarea.fill(cover_letter)
                        logger.info("Cover letter filled")
                    return
            except Exception as e:
                logger.debug(f"Cover letter handling error: {e}")

    async def _fill_text_fields(self, user_profile: Dict[str, Any]):
        """Fill visible text input fields using profile data."""
        from worker.automation.form_filler import FormFiller
        filler = FormFiller()

        # Query inputs inside the modal context
        modal = await self._get_modal()
        scope = modal if modal else self.page

        text_inputs = await scope.query_selector_all(
            'input[type="text"], input[type="number"], '
            'input[type="tel"], input[type="email"], '
            'input:not([type])'
        )

        for input_el in text_inputs:
            try:
                # Skip hidden inputs
                if not await input_el.is_visible():
                    continue

                # Skip file inputs that weren't caught above
                input_type = await input_el.get_attribute("type")
                if input_type in ("file", "hidden"):
                    continue

                # Skip if already filled (input_value reflects actual form state)
                current_value = await input_el.input_value() or ""
                if current_value.strip():
                    continue

                # Skip typeahead fields - they'll be handled by _handle_typeahead_fields
                is_typeahead = await input_el.evaluate(
                    'el => !!(el.closest("[role=combobox]") || '
                    'el.getAttribute("aria-autocomplete") || '
                    'el.closest(".artdeco-typeahead") || '
                    'el.closest("[class*=typeahead]"))'
                )
                if is_typeahead:
                    continue

                # Get label or placeholder for context
                label = await self._get_field_label(input_el)
                if not label:
                    continue

                # Map to profile field
                value = filler.get_field_value(label, user_profile)
                if value:
                    await input_el.click()
                    await input_el.fill(str(value))
                    logger.info(f"Filled text field '{label}' with profile data")
                    await self.random_delay(0.3, 0.8)
            except Exception as e:
                logger.debug(f"Failed to fill text field: {e}")

    async def _fill_select_fields(self, user_profile: Dict[str, Any]):
        """Fill select/dropdown fields."""
        from worker.automation.form_filler import FormFiller
        filler = FormFiller()

        modal = await self._get_modal()
        scope = modal if modal else self.page

        # Handle native <select> elements
        selects = await scope.query_selector_all("select")
        for select in selects:
            try:
                if not await select.is_visible():
                    continue

                # Check if already has a non-default selection
                current_val = await select.evaluate(
                    'el => el.options[el.selectedIndex]?.text || ""'
                )
                if current_val and current_val.strip() and \
                   current_val.lower() not in ("select an option", "select", "--", ""):
                    continue

                label = await self._get_field_label(select)
                if not label:
                    continue

                value = filler.get_select_value(label, user_profile)
                if value:
                    try:
                        await select.select_option(label=value)
                    except Exception:
                        try:
                            await select.select_option(value=value)
                        except Exception:
                            # Try partial text match
                            options = await select.query_selector_all("option")
                            for opt in options:
                                opt_text = (await opt.text_content() or "").strip()
                                if value.lower() in opt_text.lower():
                                    opt_value = await opt.get_attribute("value")
                                    if opt_value:
                                        await select.select_option(value=opt_value)
                                        break
                    logger.info(f"Filled select '{label}'")
                    await self.random_delay(0.3, 0.5)
            except Exception as e:
                logger.debug(f"Failed to fill select: {e}")

    async def _fill_radio_fields(self, user_profile: Dict[str, Any]):
        """Fill radio button groups (native input[type=radio] AND custom role=radio)."""
        from worker.automation.form_filler import FormFiller
        filler = FormFiller()

        modal = await self._get_modal()
        scope = modal if modal else self.page

        fieldsets = await scope.query_selector_all(
            'fieldset, [role="radiogroup"], [role="group"]'
        )
        for fieldset in fieldsets:
            try:
                if not await fieldset.is_visible():
                    continue

                # Check if already answered - native or custom radio
                checked = await fieldset.query_selector(
                    'input[type="radio"]:checked, '
                    '[role="radio"][aria-checked="true"], '
                    '[data-test-text-selectable-option][aria-checked="true"]'
                )
                if checked:
                    continue

                legend = await fieldset.query_selector(
                    "legend, label, span.t-14, .fb-form-element-label"
                )
                if not legend:
                    continue

                label_text = (await legend.text_content() or "").strip()
                if not label_text:
                    continue

                answer = filler.get_radio_value(label_text, user_profile)

                if answer:
                    # Try native radio buttons first
                    radios = await fieldset.query_selector_all('input[type="radio"]')
                    clicked = False
                    for radio in radios:
                        radio_label = await self._get_field_label(radio)
                        if radio_label and answer.lower() in radio_label.lower():
                            await radio.click()
                            logger.info(f"Selected radio '{answer}' for '{label_text[:50]}'")
                            await self.random_delay(0.2, 0.5)
                            clicked = True
                            break

                    # Try custom role="radio" elements (LinkedIn Artdeco)
                    if not clicked:
                        custom_radios = await fieldset.query_selector_all(
                            '[role="radio"], [data-test-text-selectable-option]'
                        )
                        for custom_radio in custom_radios:
                            radio_text = (await custom_radio.text_content() or "").strip()
                            if radio_text and answer.lower() in radio_text.lower():
                                await custom_radio.click()
                                logger.info(f"Selected custom radio '{answer}' for '{label_text[:50]}'")
                                await self.random_delay(0.2, 0.5)
                                break
            except Exception as e:
                logger.debug(f"Failed to fill radio: {e}")

    async def _fill_checkbox_fields(self, user_profile: Dict[str, Any]):
        """Fill checkbox fields (typically for agreements/terms)."""
        modal = await self._get_modal()
        scope = modal if modal else self.page

        checkboxes = await scope.query_selector_all('input[type="checkbox"]')
        for checkbox in checkboxes:
            try:
                if not await checkbox.is_visible():
                    continue

                # Skip if already checked
                is_checked = await checkbox.is_checked()
                if is_checked:
                    continue

                label = await self._get_field_label(checkbox)
                if label and any(word in label.lower() for word in [
                    "agree", "terms", "acknowledge", "confirm", "certify"
                ]):
                    await checkbox.click()
                    logger.info(f"Checked agreement checkbox: '{label[:50]}'")
                    await self.random_delay(0.2, 0.4)
            except Exception:
                pass

    async def _handle_screening_questions(
        self, user_profile: Dict[str, Any], job_details: Dict[str, Any]
    ):
        """Handle screening questions using AI for fields not filled by profile mapping."""
        modal = await self._get_modal()
        scope = modal if modal else self.page

        question_containers = await scope.query_selector_all(FORM_SECTION_SELECTORS)
        if not question_containers:
            return

        # Lazy-init the answerer only when needed
        answerer = None

        for container in question_containers:
            try:
                if not await container.is_visible():
                    continue

                # Get question text
                question_el = await container.query_selector(
                    "label, .fb-dash-form-element__label, .fb-form-element-label, "
                    "span.t-14, legend"
                )
                if not question_el:
                    continue

                question_text = (await question_el.text_content() or "").strip()
                if not question_text or len(question_text) < 5:
                    continue

                # ── Text/number input ──
                text_input = await container.query_selector(
                    'input[type="text"], input[type="number"], textarea, '
                    'input:not([type])'
                )
                if text_input and await text_input.is_visible():
                    # Skip typeahead inputs - handled by _handle_typeahead_fields
                    is_typeahead = await text_input.evaluate(
                        'el => !!(el.closest("[role=combobox]") || '
                        'el.getAttribute("aria-autocomplete") || '
                        'el.closest(".artdeco-typeahead") || '
                        'el.closest("[class*=typeahead]"))'
                    )
                    if is_typeahead:
                        continue

                    # Use input_value() for accurate value detection
                    current_val = await text_input.input_value() or ""
                    if current_val.strip():
                        continue  # Already filled (by profile filler or pre-filled)

                    if not answerer:
                        from worker.ai.question_answerer import QuestionAnswerer
                        answerer = QuestionAnswerer()

                    input_type = await text_input.get_attribute("type") or "text"
                    answer = await answerer.answer_question(
                        question=question_text,
                        user_profile=user_profile,
                        job_details=job_details,
                        answer_type="number" if input_type == "number" else "text",
                    )
                    if answer:
                        await text_input.click()
                        await text_input.fill(str(answer))
                        logger.info(f"AI answered '{question_text[:50]}' -> '{answer[:30]}'")
                        await self.random_delay(0.3, 0.6)
                    continue

                # ── Select dropdown ──
                select = await container.query_selector("select")
                if select and await select.is_visible():
                    # Check if already selected (non-default)
                    current_sel = await select.evaluate(
                        'el => el.options[el.selectedIndex]?.text || ""'
                    )
                    if current_sel.strip() and current_sel.lower() not in (
                        "select an option", "select", "--", ""
                    ):
                        continue

                    options = await select.query_selector_all("option")
                    option_texts = []
                    for opt in options:
                        text = (await opt.text_content() or "").strip()
                        if text and text.lower() not in (
                            "select an option", "select", "--", ""
                        ):
                            option_texts.append(text)

                    if option_texts:
                        if not answerer:
                            from worker.ai.question_answerer import QuestionAnswerer
                            answerer = QuestionAnswerer()

                        answer = await answerer.answer_question(
                            question=question_text,
                            user_profile=user_profile,
                            job_details=job_details,
                            answer_type="select",
                            options=option_texts,
                        )
                        if answer:
                            try:
                                await select.select_option(label=answer)
                            except Exception:
                                # Find closest match
                                for opt_text in option_texts:
                                    if answer.lower() in opt_text.lower() or \
                                       opt_text.lower() in answer.lower():
                                        await select.select_option(label=opt_text)
                                        break
                            logger.info(f"AI selected '{answer}' for '{question_text[:50]}'")
                            await self.random_delay(0.3, 0.5)
                    continue

                # ── Radio buttons (native + custom role="radio") ──
                radios = await container.query_selector_all(
                    'input[type="radio"], [role="radio"], '
                    '[data-test-text-selectable-option]'
                )
                if radios:
                    # Check if already selected
                    has_checked = False
                    for r in radios:
                        try:
                            tag = await r.evaluate('el => el.tagName.toLowerCase()')
                            if tag == "input":
                                has_checked = await r.is_checked()
                            else:
                                aria_checked = await r.get_attribute("aria-checked")
                                has_checked = aria_checked == "true"
                            if has_checked:
                                break
                        except Exception:
                            continue
                    if has_checked:
                        continue

                    radio_labels = []
                    for radio in radios:
                        label = await self._get_field_label(radio)
                        if not label:
                            # For custom radios, text content IS the label
                            label = (await radio.text_content() or "").strip()
                        if label:
                            radio_labels.append(label)

                    if radio_labels:
                        if not answerer:
                            from worker.ai.question_answerer import QuestionAnswerer
                            answerer = QuestionAnswerer()

                        answer = await answerer.answer_question(
                            question=question_text,
                            user_profile=user_profile,
                            job_details=job_details,
                            answer_type="radio",
                            options=radio_labels,
                        )
                        if answer:
                            for radio, label in zip(radios, radio_labels):
                                if answer.lower() == label.lower() or \
                                   answer.lower() in label.lower():
                                    await radio.click()
                                    logger.info(
                                        f"AI selected radio '{answer}' for "
                                        f"'{question_text[:50]}'"
                                    )
                                    await self.random_delay(0.2, 0.4)
                                    break

            except Exception as e:
                logger.debug(f"Failed to handle screening question: {e}")

    # ── Validation error recovery ─────────────────────────────────────

    async def _fill_unfilled_required_fields(
        self, user_profile: Dict[str, Any], job_details: Dict[str, Any]
    ):
        """
        Fallback: find ALL empty visible form fields and fill them with AI.
        Called when validation errors persist after normal filling.
        """
        modal = await self._get_modal()
        scope = modal if modal else self.page

        from worker.ai.question_answerer import QuestionAnswerer
        answerer = QuestionAnswerer()

        # Find all visible empty text/number inputs
        all_inputs = await scope.query_selector_all(
            'input[type="text"], input[type="number"], '
            'input[type="tel"], input[type="email"], '
            'input:not([type]), textarea'
        )

        for input_el in all_inputs:
            try:
                if not await input_el.is_visible():
                    continue
                input_type = await input_el.get_attribute("type")
                if input_type in ("file", "hidden", "checkbox", "radio"):
                    continue

                current_val = await input_el.input_value() or ""
                if current_val.strip():
                    continue

                label = await self._get_field_label(input_el)
                if not label:
                    continue

                # Check if this is a typeahead
                is_typeahead = await input_el.evaluate(
                    'el => !!(el.closest("[role=combobox]") || '
                    'el.getAttribute("aria-autocomplete") || '
                    'el.closest(".artdeco-typeahead") || '
                    'el.closest("[class*=typeahead]"))'
                )

                answer = await answerer.answer_question(
                    question=label,
                    user_profile=user_profile,
                    job_details=job_details,
                    answer_type="text",
                )

                if answer:
                    if is_typeahead:
                        await input_el.click()
                        await input_el.fill("")
                        await input_el.type(str(answer), delay=80)
                        await self._select_typeahead_suggestion(scope, str(answer))
                    else:
                        await input_el.click()
                        await input_el.fill(str(answer))
                    logger.info(f"Recovery filled '{label}' -> '{str(answer)[:30]}'")
                    await self.random_delay(0.2, 0.5)
            except Exception as e:
                logger.debug(f"Recovery fill error: {e}")

        # Find all unselected native selects with default value
        selects = await scope.query_selector_all("select")
        for select in selects:
            try:
                if not await select.is_visible():
                    continue
                current_sel = await select.evaluate(
                    'el => el.options[el.selectedIndex]?.text || ""'
                )
                if current_sel.strip() and current_sel.lower() not in (
                    "select an option", "select", "--", ""
                ):
                    continue

                label = await self._get_field_label(select)
                if not label:
                    continue

                options = await select.query_selector_all("option")
                option_texts = []
                for opt in options:
                    text = (await opt.text_content() or "").strip()
                    if text and text.lower() not in (
                        "select an option", "select", "--", ""
                    ):
                        option_texts.append(text)

                if option_texts:
                    answer = await answerer.answer_question(
                        question=label,
                        user_profile=user_profile,
                        job_details=job_details,
                        answer_type="select",
                        options=option_texts,
                    )
                    if answer:
                        try:
                            await select.select_option(label=answer)
                        except Exception:
                            for opt_text in option_texts:
                                if answer.lower() in opt_text.lower():
                                    await select.select_option(label=opt_text)
                                    break
                        logger.info(f"Recovery selected '{answer}' for '{label}'")
                        await self.random_delay(0.2, 0.5)
            except Exception as e:
                logger.debug(f"Recovery select error: {e}")

        # Find unchecked radio groups
        fieldsets = await scope.query_selector_all(
            'fieldset, [role="radiogroup"], [role="group"]'
        )
        for fieldset in fieldsets:
            try:
                if not await fieldset.is_visible():
                    continue
                checked = await fieldset.query_selector(
                    'input[type="radio"]:checked, '
                    '[role="radio"][aria-checked="true"]'
                )
                if checked:
                    continue

                legend = await fieldset.query_selector(
                    "legend, label, span.t-14, .fb-form-element-label"
                )
                if not legend:
                    continue
                label_text = (await legend.text_content() or "").strip()
                if not label_text:
                    continue

                radios = await fieldset.query_selector_all(
                    'input[type="radio"], [role="radio"], '
                    '[data-test-text-selectable-option]'
                )
                radio_labels = []
                for radio in radios:
                    rl = await self._get_field_label(radio)
                    if not rl:
                        rl = (await radio.text_content() or "").strip()
                    if rl:
                        radio_labels.append(rl)

                if radio_labels:
                    answer = await answerer.answer_question(
                        question=label_text,
                        user_profile=user_profile,
                        job_details=job_details,
                        answer_type="radio",
                        options=radio_labels,
                    )
                    if answer:
                        for radio, rl in zip(radios, radio_labels):
                            if answer.lower() == rl.lower() or answer.lower() in rl.lower():
                                await radio.click()
                                logger.info(f"Recovery radio '{answer}' for '{label_text[:40]}'")
                                await self.random_delay(0.2, 0.4)
                                break
            except Exception as e:
                logger.debug(f"Recovery radio error: {e}")

    # ── Typeahead / autocomplete handling ─────────────────────────────

    async def _handle_typeahead_fields(
        self, user_profile: Dict[str, Any], job_details: Dict[str, Any]
    ):
        """
        Handle LinkedIn's custom typeahead/autocomplete dropdowns.

        LinkedIn uses Artdeco typeahead components instead of native <select>
        for fields like City, School, Company, Degree, Field of Study.
        These require: type text → wait for suggestion dropdown → click match.
        """
        modal = await self._get_modal()
        scope = modal if modal else self.page

        # Find all typeahead containers in the current form step
        typeahead_containers = await scope.query_selector_all(
            '.artdeco-typeahead, '
            '[class*="typeahead"], '
            '[role="combobox"], '
            '[class*="text-input--has-typeahead"]'
        )

        # Also find inputs with aria-autocomplete attribute
        autocomplete_inputs = await scope.query_selector_all(
            'input[aria-autocomplete="list"], '
            'input[aria-autocomplete="both"]'
        )

        # Merge: get the containers for autocomplete inputs
        processed_inputs = set()
        typeahead_items = []

        for container in typeahead_containers:
            try:
                if not await container.is_visible():
                    continue
                input_el = await container.query_selector('input[type="text"], input:not([type])')
                if input_el:
                    input_id = await input_el.get_attribute("id") or id(input_el)
                    if input_id not in processed_inputs:
                        processed_inputs.add(input_id)
                        typeahead_items.append((container, input_el))
            except Exception:
                continue

        for input_el in autocomplete_inputs:
            try:
                if not await input_el.is_visible():
                    continue
                input_id = await input_el.get_attribute("id") or id(input_el)
                if input_id not in processed_inputs:
                    processed_inputs.add(input_id)
                    # Find parent container
                    container = await input_el.evaluate_handle(
                        'el => el.closest(".artdeco-typeahead") || '
                        'el.closest("[class*=typeahead]") || '
                        'el.closest("[role=combobox]") || '
                        'el.parentElement'
                    )
                    typeahead_items.append((container, input_el))
            except Exception:
                continue

        if not typeahead_items:
            return

        from worker.automation.form_filler import FormFiller
        filler = FormFiller()

        for container, input_el in typeahead_items:
            try:
                # Skip if already has a value selected
                current_val = await input_el.input_value() or ""
                if current_val.strip():
                    # Check if the typeahead has accepted the value
                    # (aria-expanded should be false when a selection is confirmed)
                    is_expanded = await input_el.get_attribute("aria-expanded")
                    if is_expanded != "true":
                        continue

                # Get the field label
                label = await self._get_field_label(input_el)
                if not label:
                    # Try getting label from the container
                    label = await self._get_field_label(container)
                if not label:
                    continue

                # Get value from profile mapping first
                value = filler.get_field_value(label, user_profile)

                # If no profile mapping, try AI
                if not value:
                    from worker.ai.question_answerer import QuestionAnswerer
                    answerer = QuestionAnswerer()
                    value = await answerer.answer_question(
                        question=label,
                        user_profile=user_profile,
                        job_details=job_details,
                        answer_type="text",
                    )

                if not value:
                    continue

                # Type into the typeahead input to trigger suggestions
                await input_el.click()
                await asyncio.sleep(0.3)

                # Clear existing value first
                await input_el.fill("")
                await asyncio.sleep(0.2)

                # Type the value character-by-character (more natural, triggers autocomplete)
                await input_el.type(str(value), delay=80)
                logger.info(f"Typed '{value}' into typeahead field '{label}'")

                # Wait for suggestion dropdown to appear
                suggestion_selected = await self._select_typeahead_suggestion(
                    scope, value
                )

                if suggestion_selected:
                    logger.info(f"Selected typeahead suggestion for '{label}'")
                else:
                    # Fallback: try pressing Enter to accept top suggestion
                    await self.page.keyboard.press("ArrowDown")
                    await asyncio.sleep(0.2)
                    await self.page.keyboard.press("Enter")
                    logger.info(f"Pressed Enter for typeahead '{label}' (no exact match)")

                await self.random_delay(0.3, 0.8)

            except Exception as e:
                logger.debug(f"Typeahead handling error for field: {e}")

    async def _select_typeahead_suggestion(
        self, scope, target_value: str, timeout: int = 3000
    ) -> bool:
        """
        Wait for typeahead suggestion dropdown and click the best match.

        LinkedIn typeahead suggestions appear in:
        - [role="listbox"] > [role="option"]
        - .artdeco-typeahead__results-list > li
        - .basic-typeahead__selectable > li
        """
        target_lower = target_value.lower().strip()

        # Wait for suggestion list to appear
        suggestion_selectors = [
            '[role="listbox"]',
            '.artdeco-typeahead__results-list',
            '.basic-typeahead__selectable',
            '[class*="typeahead__results"]',
        ]

        listbox = None
        for selector in suggestion_selectors:
            try:
                listbox = await self.page.wait_for_selector(
                    selector, state="visible", timeout=timeout
                )
                if listbox:
                    break
            except Exception:
                continue

        if not listbox:
            return False

        await asyncio.sleep(0.5)  # Let suggestions fully render

        # Get all option elements
        options = await listbox.query_selector_all(
            '[role="option"], li, .artdeco-typeahead__result'
        )

        if not options:
            return False

        # Find the best matching option
        best_match = None
        best_score = 0

        for option in options:
            try:
                if not await option.is_visible():
                    continue
                opt_text = (await option.text_content() or "").strip().lower()
                if not opt_text:
                    continue

                # Exact match
                if opt_text == target_lower:
                    await option.click()
                    return True

                # Calculate match score
                score = 0
                if target_lower in opt_text:
                    score = len(target_lower) / len(opt_text) * 100
                elif opt_text in target_lower:
                    score = len(opt_text) / len(target_lower) * 80

                # Word overlap scoring
                if score == 0:
                    target_words = set(target_lower.split())
                    opt_words = set(opt_text.split())
                    overlap = target_words & opt_words
                    if overlap:
                        score = len(overlap) / max(len(target_words), 1) * 60

                if score > best_score:
                    best_score = score
                    best_match = option
            except Exception:
                continue

        # Click the best match if score is reasonable
        if best_match and best_score > 30:
            try:
                await best_match.click()
                return True
            except Exception:
                pass

        # Fallback: click the first visible option
        for option in options:
            try:
                if await option.is_visible():
                    await option.click()
                    return True
            except Exception:
                continue

        return False

    # ── Field label detection ─────────────────────────────────────────

    async def _get_field_label(self, element) -> Optional[str]:
        """Get the label text for a form field."""
        try:
            # Try aria-label
            aria_label = await element.get_attribute("aria-label")
            if aria_label and aria_label.strip():
                return aria_label.strip()

            # Try associated label via id
            field_id = await element.get_attribute("id")
            if field_id:
                label = await self.page.query_selector(f'label[for="{field_id}"]')
                if label:
                    text = (await label.text_content() or "").strip()
                    if text:
                        return text

            # Try parent form grouping label
            label_text = await element.evaluate("""el => {
                // Walk up to find the closest form grouping
                let parent = el.closest(
                    '.jobs-easy-apply-form-section__grouping, ' +
                    '.fb-dash-form-element, ' +
                    '[class*="form-component"], ' +
                    'label, .artdeco-text-input'
                );
                if (parent) {
                    let label = parent.querySelector(
                        'label, .fb-dash-form-element__label, ' +
                        '.fb-form-element-label, span.t-14, legend'
                    );
                    if (label) return label.textContent.trim();
                }
                // Try closest label
                let closestLabel = el.closest('label');
                if (closestLabel) return closestLabel.textContent.trim();
                // Try preceding sibling
                let prev = el.previousElementSibling;
                if (prev && (prev.tagName === 'LABEL' || prev.tagName === 'SPAN')) {
                    return prev.textContent.trim();
                }
                return '';
            }""")
            if label_text:
                return label_text

            # Try placeholder
            placeholder = await element.get_attribute("placeholder")
            if placeholder and placeholder.strip():
                return placeholder.strip()

        except Exception:
            pass

        return None

    # ── Form navigation ───────────────────────────────────────────────

    async def _advance_form(self) -> bool:
        """Click the Next/Continue button to advance the form (scoped to modal)."""
        modal = await self._get_modal()
        scope = modal if modal else self.page

        next_selectors = [
            'button[aria-label="Continue to next step"]',
            'button[aria-label="Review your application"]',
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button:has-text("Review")',
        ]

        for selector in next_selectors:
            try:
                button = await scope.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    logger.info(f"Clicked advance button: {selector}")
                    await self.random_delay(1.5, 3.0)

                    # Check for validation errors after clicking
                    has_errors = await self._check_validation_errors()
                    if has_errors:
                        logger.warning("Validation errors after clicking Next")
                        return False  # Will trigger re-fill attempt

                    return True
            except Exception:
                continue

        return False

    async def _try_submit(self) -> bool:
        """Try to submit the application (scoped to modal)."""
        # Uncheck "Follow company" checkbox if present
        await self._uncheck_follow_company()

        modal = await self._get_modal()
        scope = modal if modal else self.page

        submit_selectors = [
            'button[aria-label="Submit application"]',
            'button:has-text("Submit application")',
            'button:has-text("Submit")',
        ]

        for selector in submit_selectors:
            try:
                button = await scope.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    logger.info(f"Clicked submit button: {selector}")
                    await self.random_delay(2.0, 4.0)
                    return True
            except Exception:
                continue

        return False

    async def _click_primary_button(self) -> bool:
        """Fallback: click any primary action button in the modal footer."""
        try:
            button = await self.page.query_selector(
                "footer button.artdeco-button--primary, "
                ".artdeco-modal footer button.artdeco-button--primary"
            )
            if button and await button.is_visible():
                btn_text = (await button.text_content() or "").strip()
                # Don't click Dismiss/Close/Cancel buttons
                if btn_text.lower() not in ("dismiss", "close", "cancel", "discard"):
                    await button.click()
                    logger.info(f"Clicked fallback primary button: '{btn_text}'")
                    await self.random_delay(1.5, 3.0)
                    return True
        except Exception:
            pass
        return False

    async def _uncheck_follow_company(self):
        """Uncheck the 'Follow company' checkbox on the review step."""
        modal = await self._get_modal()
        scope = modal if modal else self.page

        try:
            follow_selectors = [
                'input#follow-company-checkbox',
                'input[id*="follow-company"]',
                'input[id*="follow"]',
                'label[for*="follow"] input[type="checkbox"]',
            ]
            for selector in follow_selectors:
                follow_checkbox = await scope.query_selector(selector)
                if follow_checkbox:
                    try:
                        is_checked = await follow_checkbox.is_checked()
                        if is_checked:
                            await follow_checkbox.click()
                            logger.info("Unchecked 'Follow company' checkbox")
                            await self.random_delay(0.2, 0.4)
                    except Exception:
                        # Some checkboxes need label click instead
                        label = await scope.query_selector(
                            f'label[for="{await follow_checkbox.get_attribute("id") or ""}"]'
                        )
                        if label:
                            await label.click()
                    break
        except Exception:
            pass

    # ── Validation and success checks ─────────────────────────────────

    async def _check_validation_errors(self) -> bool:
        """Check if there are validation error messages on the form."""
        modal = await self._get_modal()
        scope = modal if modal else self.page

        try:
            errors = await scope.query_selector_all(
                '.artdeco-inline-feedback--error, '
                '.artdeco-inline-feedback__message[aria-live="assertive"], '
                '[class*="form-error"], '
                '.fb-form-element-error, '
                '[data-test-form-element-error]'
            )
            for error in errors:
                if await error.is_visible():
                    error_text = (await error.text_content() or "").strip()
                    if error_text:
                        logger.warning(f"Form validation error: {error_text}")
                        return True
        except Exception:
            pass
        return False

    async def _check_submission_success(self) -> bool:
        """Check if the application was successfully submitted."""
        success_indicators = [
            'h3:has-text("Application sent")',
            'h3:has-text("Your application was sent")',
            'h2#post-apply-modal',
            'h2:has-text("Application sent")',
            '[class*="post-apply"]',
            '.artdeco-inline-feedback--success',
            'span:has-text("Application submitted")',
            '[class*="jpac-modal"]',  # LinkedIn post-apply confirmation modal
        ]

        for selector in success_indicators:
            try:
                el = await self.page.query_selector(selector)
                if el and await el.is_visible():
                    logger.info(f"Success indicator found: {selector}")
                    return True
            except Exception:
                continue

        # Check for "Done" button only in post-apply context (not general modals)
        try:
            done_btn = await self.page.query_selector('button:has-text("Done")')
            if done_btn and await done_btn.is_visible():
                # Verify it's in a post-apply modal, not the form itself
                is_post_apply = await done_btn.evaluate(
                    'el => !!(el.closest("[class*=post-apply]") || '
                    'el.closest("[id*=post-apply]") || '
                    'document.querySelector("h3")?.textContent?.includes("Application sent"))'
                )
                if is_post_apply:
                    logger.info("Success indicator found: Done button in post-apply modal")
                    return True
        except Exception:
            pass

        # Check page text
        try:
            body_text = await self.get_page_text()
            lower = body_text.lower()
            if "application was sent" in lower:
                return True
            if "application submitted" in lower:
                return True
        except Exception:
            pass

        return False
