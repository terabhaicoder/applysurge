"""
Email sending via SendGrid with tracking.

Supports tracked cold emails with open pixel and link wrapping,
as well as standard transactional emails.
"""

import logging
import os
import uuid
import re
from typing import Dict, Any, Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, From, To, Subject, Content, MimeType,
    Attachment, FileContent, FileName, FileType, Disposition,
    TrackingSettings, ClickTracking, OpenTracking,
    Header, CustomArg,
)

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
TRACKING_DOMAIN = os.environ.get("TRACKING_DOMAIN", "track.jobpilot.ai")
APP_DOMAIN = os.environ.get("APP_DOMAIN", "app.jobpilot.ai")


class EmailSender:
    """SendGrid email sender with open/click tracking."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or SENDGRID_API_KEY
        self._client = None

    @property
    def client(self) -> SendGridAPIClient:
        """Get or create SendGrid client."""
        if self._client is None:
            self._client = SendGridAPIClient(api_key=self.api_key)
        return self._client

    async def send_tracked_email(
        self,
        email_id: str,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body: str,
        signature: str = "",
        resume_url: Optional[str] = None,
        is_followup: bool = False,
        original_message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a tracked cold email with open pixel and link wrapping.

        Args:
            email_id: Internal email ID for tracking
            from_email: Sender email address
            from_name: Sender display name
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            signature: Email signature to append
            resume_url: Optional URL to attach resume
            is_followup: Whether this is a followup email
            original_message_id: Message-ID of original for threading

        Returns:
            Dict with success status, message_id, and tracking_id
        """
        try:
            tracking_id = str(uuid.uuid4())

            # Build HTML body with tracking
            html_body = self._build_tracked_html(
                body=body,
                signature=signature,
                email_id=email_id,
                tracking_id=tracking_id,
            )

            # Create mail object
            message = Mail(
                from_email=From(from_email, from_name),
                to_emails=To(to_email),
                subject=Subject(subject),
            )

            # Add plain text version
            plain_content = f"{body}\n\n{signature}".strip()
            message.add_content(Content(MimeType.text, plain_content))

            # Add HTML version with tracking
            message.add_content(Content(MimeType.html, html_body))

            # Add custom args for webhook identification
            message.add_custom_arg(CustomArg("email_id", email_id))
            message.add_custom_arg(CustomArg("tracking_id", tracking_id))

            # Threading headers for followups
            if is_followup and original_message_id:
                message.add_header(Header("In-Reply-To", original_message_id))
                message.add_header(Header("References", original_message_id))

            # Configure tracking
            tracking = TrackingSettings()
            tracking.click_tracking = ClickTracking(enable=True, enable_text=False)
            tracking.open_tracking = OpenTracking(
                enable=True,
                substitution_tag=None,
            )
            message.tracking_settings = tracking

            # Add resume as attachment if provided
            if resume_url:
                await self._attach_resume(message, resume_url)

            # Send via SendGrid
            response = self.client.send(message)

            # Extract message ID from response headers
            message_id = ""
            if hasattr(response, "headers"):
                message_id = response.headers.get("X-Message-Id", "")

            logger.info(
                f"Email sent successfully to {to_email} "
                f"(status: {response.status_code}, tracking: {tracking_id})"
            )

            return {
                "success": True,
                "message_id": message_id,
                "tracking_id": tracking_id,
                "status_code": response.status_code,
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tracking_id": tracking_id if "tracking_id" in locals() else "",
            }

    async def send_email(
        self,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a standard (non-tracked) email.
        Used for notifications, summaries, and transactional emails.

        Args:
            from_email: Sender email
            from_name: Sender name
            to_email: Recipient email
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML

        Returns:
            Dict with success status
        """
        try:
            message = Mail(
                from_email=From(from_email, from_name),
                to_emails=To(to_email),
                subject=Subject(subject),
            )

            mime_type = MimeType.html if is_html else MimeType.text
            message.add_content(Content(mime_type, body))

            # Disable tracking for transactional emails
            tracking = TrackingSettings()
            tracking.click_tracking = ClickTracking(enable=False)
            tracking.open_tracking = OpenTracking(enable=False)
            message.tracking_settings = tracking

            response = self.client.send(message)

            return {
                "success": True,
                "status_code": response.status_code,
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {"success": False, "error": str(e)}

    def _build_tracked_html(
        self,
        body: str,
        signature: str,
        email_id: str,
        tracking_id: str,
    ) -> str:
        """
        Build HTML email with open tracking pixel and wrapped links.
        """
        # Convert plain text to HTML paragraphs
        paragraphs = body.split("\n\n")
        html_paragraphs = []
        for para in paragraphs:
            # Convert single newlines to <br>
            para_html = para.replace("\n", "<br>")
            html_paragraphs.append(f"<p style='margin: 0 0 12px 0; line-height: 1.5;'>{para_html}</p>")

        body_html = "\n".join(html_paragraphs)

        # Wrap links with tracking redirects
        body_html = self._wrap_links(body_html, email_id, tracking_id)

        # Build signature HTML
        sig_html = ""
        if signature:
            sig_lines = signature.replace("\n", "<br>")
            sig_html = f"""
            <div style="margin-top: 20px; padding-top: 12px; border-top: 1px solid #e0e0e0; color: #555; font-size: 13px;">
                {sig_lines}
            </div>"""

        # Open tracking pixel
        pixel_url = f"https://{TRACKING_DOMAIN}/track/open/{email_id}/{tracking_id}"

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; color: #333; max-width: 600px;">
    {body_html}
    {sig_html}
    <img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />
</body>
</html>"""

        return html

    def _wrap_links(self, html: str, email_id: str, tracking_id: str) -> str:
        """Wrap links with click tracking redirects."""
        def replace_link(match):
            original_url = match.group(1)
            # Don't wrap tracking pixel or internal links
            if TRACKING_DOMAIN in original_url or "jobpilot" in original_url:
                return match.group(0)
            tracking_url = (
                f"https://{TRACKING_DOMAIN}/track/click/{email_id}/{tracking_id}"
                f"?url={original_url}"
            )
            return f'href="{tracking_url}"'

        # Replace href URLs
        return re.sub(r'href="([^"]+)"', replace_link, html)

    async def _attach_resume(self, message: Mail, resume_url: str):
        """Download and attach resume to email."""
        try:
            import httpx
            import base64

            async with httpx.AsyncClient() as client:
                response = await client.get(resume_url, timeout=10)
                if response.status_code == 200:
                    file_content = base64.b64encode(response.content).decode()

                    # Determine file type
                    content_type = response.headers.get("content-type", "application/pdf")
                    extension = "pdf" if "pdf" in content_type else "docx"

                    attachment = Attachment()
                    attachment.file_content = FileContent(file_content)
                    attachment.file_name = FileName(f"resume.{extension}")
                    attachment.file_type = FileType(content_type)
                    attachment.disposition = Disposition("attachment")

                    message.add_attachment(attachment)
                    logger.info("Resume attached to email")

        except Exception as e:
            logger.warning(f"Failed to attach resume: {e}")

    async def check_bounce(self, email: str) -> bool:
        """Check if an email address has bounced previously."""
        try:
            response = self.client.client.suppression.bounces.get(
                query_params={"email": email}
            )
            bounces = response.to_dict if hasattr(response, "to_dict") else []
            return len(bounces) > 0
        except Exception:
            return False
