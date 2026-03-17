"""
Email settings management service.
"""

from datetime import datetime, timezone
from uuid import UUID

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import encrypt_value, decrypt_value
from app.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
from app.models.email_settings import EmailSettings
from app.models.email_template import EmailTemplate
from app.schemas.email import (
    EmailSettingsResponse,
    EmailSettingsUpdate,
    SmtpConnectRequest,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    EmailTemplatePreviewResponse,
    EmailTemplateGenerateRequest,
)


class EmailService:
    """Service for email settings and template management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, user_id: UUID) -> EmailSettingsResponse:
        """Get email settings for user."""
        result = await self.db.execute(
            select(EmailSettings).where(EmailSettings.user_id == user_id)
        )
        email_settings = result.scalar_one_or_none()

        if not email_settings:
            email_settings = EmailSettings(user_id=user_id)
            self.db.add(email_settings)
            await self.db.flush()
            await self.db.refresh(email_settings)

        return EmailSettingsResponse(
            id=email_settings.id,
            user_id=email_settings.user_id,
            provider=email_settings.provider or "smtp",
            smtp_host=email_settings.smtp_host,
            smtp_port=email_settings.smtp_port,
            smtp_username=email_settings.smtp_username,
            smtp_use_tls=email_settings.smtp_use_tls,
            from_email=email_settings.from_email,
            from_name=email_settings.from_name,
            signature=email_settings.signature_text,
            daily_send_limit=email_settings.max_emails_per_day,
            enabled=email_settings.oauth_connected or email_settings.smtp_host is not None,
            is_verified=email_settings.is_verified,
            created_at=email_settings.created_at,
            updated_at=email_settings.updated_at,
        )

    async def update_settings(
        self, user_id: UUID, data: EmailSettingsUpdate
    ) -> EmailSettingsResponse:
        """Update email settings."""
        result = await self.db.execute(
            select(EmailSettings).where(EmailSettings.user_id == user_id)
        )
        email_settings = result.scalar_one_or_none()

        if not email_settings:
            email_settings = EmailSettings(user_id=user_id)
            self.db.add(email_settings)
            await self.db.flush()
            await self.db.refresh(email_settings)

        update_data = data.model_dump(exclude_unset=True)

        # Map schema fields to model fields
        if "smtp_password" in update_data and update_data["smtp_password"]:
            email_settings.encrypted_smtp_password = encrypt_value(update_data.pop("smtp_password"))
        else:
            update_data.pop("smtp_password", None)

        if "signature" in update_data:
            email_settings.signature_text = update_data.pop("signature")

        if "daily_send_limit" in update_data:
            email_settings.max_emails_per_day = update_data.pop("daily_send_limit")

        # Apply remaining fields directly
        for field, value in update_data.items():
            if hasattr(email_settings, field):
                setattr(email_settings, field, value)

        await self.db.flush()
        await self.db.refresh(email_settings)

        return await self.get_settings(user_id)

    async def connect_gmail(self, user_id: UUID, authorization_code: str) -> EmailSettingsResponse:
        """Connect Gmail via OAuth."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": authorization_code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": f"{settings.CORS_ORIGINS[0]}/settings/email/callback",
                    "grant_type": "authorization_code",
                },
            )

        if response.status_code != 200:
            raise ExternalServiceError("Google", "Failed to exchange authorization code")

        token_data = response.json()

        result = await self.db.execute(
            select(EmailSettings).where(EmailSettings.user_id == user_id)
        )
        email_settings = result.scalar_one_or_none()

        if not email_settings:
            email_settings = EmailSettings(user_id=user_id)
            self.db.add(email_settings)

        email_settings.provider = "gmail"
        email_settings.smtp_host = "smtp.gmail.com"
        email_settings.smtp_port = 587
        email_settings.smtp_use_tls = True
        email_settings.oauth_connected = True
        email_settings.encrypted_oauth_token = encrypt_value(token_data.get("access_token", ""))
        email_settings.encrypted_oauth_refresh_token = encrypt_value(token_data.get("refresh_token", ""))
        email_settings.is_verified = True

        await self.db.flush()
        await self.db.refresh(email_settings)

        return await self.get_settings(user_id)

    async def connect_smtp(
        self, user_id: UUID, data: SmtpConnectRequest
    ) -> EmailSettingsResponse:
        """Connect via SMTP settings."""
        result = await self.db.execute(
            select(EmailSettings).where(EmailSettings.user_id == user_id)
        )
        email_settings = result.scalar_one_or_none()

        if not email_settings:
            email_settings = EmailSettings(user_id=user_id)
            self.db.add(email_settings)

        email_settings.provider = "smtp"
        email_settings.smtp_host = data.host
        email_settings.smtp_port = data.port
        email_settings.smtp_username = data.username
        email_settings.encrypted_smtp_password = encrypt_value(data.password)
        email_settings.smtp_use_tls = data.use_tls
        email_settings.from_email = data.from_email
        email_settings.from_name = data.from_name

        await self.db.flush()
        await self.db.refresh(email_settings)

        return await self.get_settings(user_id)

    async def verify_connection(self, user_id: UUID) -> bool:
        """Verify email connection by attempting to connect to SMTP."""
        result = await self.db.execute(
            select(EmailSettings).where(EmailSettings.user_id == user_id)
        )
        email_settings = result.scalar_one_or_none()

        if not email_settings:
            raise NotFoundError("Email settings")

        try:
            password = decrypt_value(email_settings.encrypted_smtp_password or "")
            smtp = aiosmtplib.SMTP(
                hostname=email_settings.smtp_host or settings.SMTP_HOST,
                port=email_settings.smtp_port or settings.SMTP_PORT,
                use_tls=email_settings.smtp_use_tls,
            )
            await smtp.connect()
            if password and email_settings.smtp_username:
                await smtp.login(email_settings.smtp_username, password)
            await smtp.quit()

            email_settings.is_verified = True
            await self.db.flush()

            return True
        except Exception as e:
            raise ExternalServiceError("SMTP", f"Connection failed: {str(e)}")

    async def send_test_email(self, user_id: UUID, to_email: str, subject: str) -> bool:
        """Send a test email."""
        result = await self.db.execute(
            select(EmailSettings).where(EmailSettings.user_id == user_id)
        )
        email_settings = result.scalar_one_or_none()

        if not email_settings or not email_settings.is_verified:
            raise ValidationError("Email settings not configured or verified")

        try:
            password = decrypt_value(email_settings.encrypted_smtp_password or "")

            msg = MIMEMultipart()
            msg["From"] = f"{email_settings.from_name or 'JobPilot'} <{email_settings.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            body = "This is a test email from JobPilot. Your email configuration is working correctly."
            msg.attach(MIMEText(body, "plain"))

            smtp = aiosmtplib.SMTP(
                hostname=email_settings.smtp_host or settings.SMTP_HOST,
                port=email_settings.smtp_port or settings.SMTP_PORT,
                use_tls=email_settings.smtp_use_tls,
            )
            await smtp.connect()
            if password and email_settings.smtp_username:
                await smtp.login(email_settings.smtp_username, password)
            await smtp.send_message(msg)
            await smtp.quit()

            return True
        except Exception as e:
            raise ExternalServiceError("SMTP", f"Failed to send test email: {str(e)}")

    # Template operations
    async def list_templates(self, user_id: UUID) -> list[EmailTemplateResponse]:
        """List all email templates for user."""
        result = await self.db.execute(
            select(EmailTemplate)
            .where(EmailTemplate.user_id == user_id, EmailTemplate.is_active == True)
            .order_by(EmailTemplate.created_at.desc())
        )
        templates = result.scalars().all()
        return [self._template_to_response(t) for t in templates]

    async def get_template(self, user_id: UUID, template_id: UUID) -> EmailTemplateResponse:
        """Get a specific template."""
        template = await self._get_user_template(user_id, template_id)
        return self._template_to_response(template)

    async def create_template(
        self, user_id: UUID, data: EmailTemplateCreate
    ) -> EmailTemplateResponse:
        """Create a new email template."""
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", data.name.lower()).strip("-")

        template = EmailTemplate(
            user_id=user_id,
            name=data.name,
            slug=slug,
            subject=data.subject,
            body_text=data.body,
            category=data.template_type,
            available_variables=data.variables,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return self._template_to_response(template)

    async def update_template(
        self, user_id: UUID, template_id: UUID, data: EmailTemplateUpdate
    ) -> EmailTemplateResponse:
        """Update an email template."""
        template = await self._get_user_template(user_id, template_id)

        update_data = data.model_dump(exclude_unset=True)

        if "body" in update_data:
            template.body_text = update_data.pop("body")
        if "template_type" in update_data:
            template.category = update_data.pop("template_type")
        if "variables" in update_data:
            template.available_variables = update_data.pop("variables")

        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)

        await self.db.flush()
        await self.db.refresh(template)

        return self._template_to_response(template)

    async def delete_template(self, user_id: UUID, template_id: UUID) -> bool:
        """Delete an email template."""
        template = await self._get_user_template(user_id, template_id)
        template.is_active = False
        await self.db.flush()
        return True

    async def preview_template(
        self, user_id: UUID, template_id: UUID, variables: dict[str, str]
    ) -> EmailTemplatePreviewResponse:
        """Preview a template with variable substitution."""
        template = await self._get_user_template(user_id, template_id)
        rendered_subject, rendered_body = template.render(variables)
        return EmailTemplatePreviewResponse(subject=rendered_subject, body=rendered_body)

    async def generate_template(
        self, user_id: UUID, data: EmailTemplateGenerateRequest
    ) -> EmailTemplateResponse:
        """Generate an email template using AI."""
        from app.services.llm_service import LLMService

        llm = LLMService()
        prompt = self._build_generation_prompt(data)
        generated = await llm.generate_text(prompt)

        # Parse generated content
        parts = generated.split("----", 1)
        subject = parts[0].strip().removeprefix("Subject:").strip() if parts else f"RE: {data.job_title or 'Application'}"
        body = parts[1].strip() if len(parts) > 1 else generated

        import re
        slug = re.sub(r"[^a-z0-9]+", "-", f"ai-{data.template_type}".lower()).strip("-")

        template = EmailTemplate(
            user_id=user_id,
            name=f"AI Generated - {data.template_type.replace('_', ' ').title()}",
            slug=f"{slug}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            subject=subject,
            body_text=body,
            category=data.template_type,
            ai_generated=True,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)

        return self._template_to_response(template)

    def _build_generation_prompt(self, data: EmailTemplateGenerateRequest) -> str:
        """Build prompt for template generation."""
        prompt = f"""Generate a professional email template for a job application.
Type: {data.template_type.replace('_', ' ')}
Tone: {data.tone}
"""
        if data.job_title:
            prompt += f"Job Title: {data.job_title}\n"
        if data.company:
            prompt += f"Company: {data.company}\n"
        if data.additional_context:
            prompt += f"Additional Context: {data.additional_context}\n"

        prompt += """
Use {{variable_name}} for template variables like {{name}}, {{company}}, {{position}}, {{date}}.
Format: First line is "Subject: <subject>", then "----", then the body.
Keep it concise and professional.
"""
        return prompt

    def _template_to_response(self, template: EmailTemplate) -> EmailTemplateResponse:
        """Convert EmailTemplate model to response schema."""
        return EmailTemplateResponse(
            id=template.id,
            user_id=template.user_id,
            name=template.name,
            subject=template.subject,
            body=template.body_text,
            template_type=template.category,
            variables=template.available_variables,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    async def _get_user_template(self, user_id: UUID, template_id: UUID) -> EmailTemplate:
        """Get template belonging to user."""
        result = await self.db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == template_id,
                EmailTemplate.user_id == user_id,
                EmailTemplate.is_active == True,
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundError("Email template")
        return template
