"""
Email response parser.

Parses incoming email responses from webhooks or IMAP,
extracts relevant content, and triggers classification.
"""

import logging
import re
import email
from email import policy
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EmailParser:
    """
    Parses incoming email responses and extracts structured content.
    Handles various email formats, HTML stripping, and quote removal.
    """

    # Patterns that indicate the start of a quoted reply
    QUOTE_PATTERNS = [
        r"^On .+ wrote:$",
        r"^-{3,}\s*Original Message\s*-{3,}$",
        r"^>{1,}",
        r"^From:.+",
        r"^Sent:.+",
        r"^_{3,}$",
        r"^-{3,}$",
    ]

    def parse_inbound_email(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse an inbound email from webhook payload.
        Supports SendGrid Inbound Parse format.

        Args:
            raw_data: Raw webhook payload

        Returns:
            Parsed email data with cleaned body
        """
        try:
            parsed = {
                "from_email": self._extract_email_address(raw_data.get("from", "")),
                "from_name": self._extract_name(raw_data.get("from", "")),
                "to_email": self._extract_email_address(raw_data.get("to", "")),
                "subject": raw_data.get("subject", "").strip(),
                "body": "",
                "html_body": "",
                "headers": {},
                "received_at": datetime.now(timezone.utc).isoformat(),
                "attachments": [],
                "in_reply_to": "",
                "references": "",
            }

            # Extract body
            text_body = raw_data.get("text", "")
            html_body = raw_data.get("html", "")

            if text_body:
                parsed["body"] = self._clean_body(text_body)
            elif html_body:
                parsed["body"] = self._html_to_text(html_body)
                parsed["html_body"] = html_body

            # Extract headers for threading
            headers_raw = raw_data.get("headers", "")
            if headers_raw:
                parsed["headers"] = self._parse_headers(headers_raw)
                parsed["in_reply_to"] = parsed["headers"].get("In-Reply-To", "")
                parsed["references"] = parsed["headers"].get("References", "")

            # Extract envelope data
            envelope = raw_data.get("envelope", "")
            if isinstance(envelope, str):
                try:
                    import json
                    envelope = json.loads(envelope)
                except (json.JSONDecodeError, TypeError):
                    envelope = {}

            if isinstance(envelope, dict):
                if not parsed["from_email"]:
                    parsed["from_email"] = envelope.get("from", "")
                if not parsed["to_email"]:
                    to_list = envelope.get("to", [])
                    parsed["to_email"] = to_list[0] if to_list else ""

            # Extract attachment info
            attachments = raw_data.get("attachments", 0)
            if isinstance(attachments, int) and attachments > 0:
                parsed["attachment_count"] = attachments
            elif isinstance(attachments, list):
                parsed["attachments"] = [
                    {
                        "filename": att.get("filename", ""),
                        "type": att.get("type", ""),
                        "size": att.get("size", 0),
                    }
                    for att in attachments
                ]

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse inbound email: {e}", exc_info=True)
            return {
                "from_email": raw_data.get("from", ""),
                "subject": raw_data.get("subject", ""),
                "body": raw_data.get("text", raw_data.get("html", "")),
                "received_at": datetime.now(timezone.utc).isoformat(),
                "parse_error": str(e),
            }

    def parse_mime_email(self, raw_mime: str) -> Dict[str, Any]:
        """
        Parse a raw MIME email message.

        Args:
            raw_mime: Raw MIME email string

        Returns:
            Parsed email data
        """
        try:
            msg = email.message_from_string(raw_mime, policy=policy.default)

            parsed = {
                "from_email": self._extract_email_address(msg.get("From", "")),
                "from_name": self._extract_name(msg.get("From", "")),
                "to_email": self._extract_email_address(msg.get("To", "")),
                "subject": msg.get("Subject", "").strip(),
                "body": "",
                "html_body": "",
                "in_reply_to": msg.get("In-Reply-To", ""),
                "references": msg.get("References", ""),
                "message_id": msg.get("Message-ID", ""),
                "date": msg.get("Date", ""),
                "received_at": datetime.now(timezone.utc).isoformat(),
            }

            # Extract body from MIME parts
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain" and not parsed["body"]:
                        payload = part.get_payload(decode=True)
                        if payload:
                            parsed["body"] = self._clean_body(
                                payload.decode("utf-8", errors="replace")
                            )
                    elif content_type == "text/html" and not parsed["html_body"]:
                        payload = part.get_payload(decode=True)
                        if payload:
                            parsed["html_body"] = payload.decode("utf-8", errors="replace")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    text = payload.decode("utf-8", errors="replace")
                    if msg.get_content_type() == "text/html":
                        parsed["html_body"] = text
                        parsed["body"] = self._html_to_text(text)
                    else:
                        parsed["body"] = self._clean_body(text)

            # Fall back to HTML body if no plain text
            if not parsed["body"] and parsed["html_body"]:
                parsed["body"] = self._html_to_text(parsed["html_body"])

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse MIME email: {e}")
            return {
                "body": raw_mime[:1000],
                "subject": "",
                "from_email": "",
                "parse_error": str(e),
            }

    def match_to_original(
        self, parsed_email: Dict[str, Any], user_id: str = None
    ) -> Optional[str]:
        """
        Match an incoming response to the original cold email.

        Uses In-Reply-To, References, and subject line matching.

        Args:
            parsed_email: Parsed email data
            user_id: Optional user ID to narrow search

        Returns:
            Original email ID or None
        """
        import os
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://jobpilot:jobpilot_pass@postgres:5432/jobpilot_db"
        )
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(database_url, pool_size=5)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Try matching by In-Reply-To header
            in_reply_to = parsed_email.get("in_reply_to", "")
            if in_reply_to:
                result = session.execute(text("""
                    SELECT id FROM cold_emails
                    WHERE message_id = :msg_id
                    LIMIT 1
                """), {"msg_id": in_reply_to})
                row = result.first()
                if row:
                    return str(row[0])

            # Try matching by References header
            references = parsed_email.get("references", "")
            if references:
                # References can contain multiple message IDs
                ref_ids = references.split()
                for ref_id in ref_ids:
                    result = session.execute(text("""
                        SELECT id FROM cold_emails
                        WHERE message_id = :msg_id
                        LIMIT 1
                    """), {"msg_id": ref_id.strip()})
                    row = result.first()
                    if row:
                        return str(row[0])

            # Try matching by recipient email and subject
            from_email = parsed_email.get("from_email", "")
            subject = parsed_email.get("subject", "")
            # Remove Re: prefix for matching
            clean_subject = re.sub(r"^(Re:\s*)+", "", subject, flags=re.IGNORECASE).strip()

            if from_email and clean_subject:
                query_params = {
                    "recipient": from_email,
                    "subject": f"%{clean_subject}%",
                }
                user_filter = ""
                if user_id:
                    user_filter = "AND user_id = :user_id"
                    query_params["user_id"] = user_id

                result = session.execute(text(f"""
                    SELECT id FROM cold_emails
                    WHERE recipient_email = :recipient
                      AND subject LIKE :subject
                      {user_filter}
                    ORDER BY sent_at DESC
                    LIMIT 1
                """), query_params)
                row = result.first()
                if row:
                    return str(row[0])

            return None

        except Exception as e:
            logger.error(f"Failed to match email to original: {e}")
            return None
        finally:
            session.close()

    def _clean_body(self, text: str) -> str:
        """Clean email body by removing quotes, signatures, and extra whitespace."""
        lines = text.split("\n")
        clean_lines = []

        for line in lines:
            # Stop at quoted content
            is_quote = False
            for pattern in self.QUOTE_PATTERNS:
                if re.match(pattern, line.strip(), re.MULTILINE):
                    is_quote = True
                    break

            if is_quote:
                break

            clean_lines.append(line)

        result = "\n".join(clean_lines).strip()

        # Remove common signature separators and everything after
        sig_patterns = [
            r"\n--\s*\n.*$",
            r"\nBest regards,?\n.*$",
            r"\nKind regards,?\n.*$",
            r"\nThanks,?\n.*$",
            r"\nSent from my .*$",
            r"\nGet Outlook for .*$",
        ]
        for pattern in sig_patterns:
            result = re.sub(pattern, "", result, flags=re.DOTALL | re.IGNORECASE)

        return result.strip()

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove style and script tags
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Convert breaks and paragraphs to newlines
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)

        # Remove all remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        import html as html_module
        text = html_module.unescape(text)

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        return self._clean_body(text.strip())

    def _extract_email_address(self, from_string: str) -> str:
        """Extract email address from a From/To header string."""
        if not from_string:
            return ""

        # Match email in angle brackets: "Name <email@domain.com>"
        match = re.search(r"<([^>]+)>", from_string)
        if match:
            return match.group(1).strip().lower()

        # Match bare email
        match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", from_string)
        if match:
            return match.group(0).strip().lower()

        return from_string.strip().lower()

    def _extract_name(self, from_string: str) -> str:
        """Extract display name from a From header string."""
        if not from_string:
            return ""

        # "Name <email>" format
        match = re.match(r"^(.+?)\s*<", from_string)
        if match:
            name = match.group(1).strip().strip('"').strip("'")
            return name

        return ""

    def _parse_headers(self, headers_str: str) -> Dict[str, str]:
        """Parse email headers string into a dictionary."""
        headers = {}
        current_key = ""
        current_value = ""

        for line in headers_str.split("\n"):
            if line.startswith((" ", "\t")) and current_key:
                # Continuation of previous header
                current_value += " " + line.strip()
            else:
                # Save previous header
                if current_key:
                    headers[current_key] = current_value

                # Parse new header
                if ":" in line:
                    key, value = line.split(":", 1)
                    current_key = key.strip()
                    current_value = value.strip()

        # Save last header
        if current_key:
            headers[current_key] = current_value

        return headers
