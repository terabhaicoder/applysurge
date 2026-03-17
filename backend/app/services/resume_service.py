"""
Resume upload, storage, and parsing service.
"""

import re
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse, ResumeUpdate, ResumeParseResponse
from app.services.resume_parser import ResumeParser
from app.services.s3_service import S3Service


ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing path separators and special characters."""
    # Strip directory components
    filename = filename.rsplit("/", 1)[-1]
    filename = filename.rsplit("\\", 1)[-1]
    # Remove non-alphanumeric chars except dot, hyphen, underscore
    filename = re.sub(r"[^\w.\-]", "_", filename)
    # Collapse multiple underscores
    filename = re.sub(r"_+", "_", filename).strip("_")
    return filename or "unnamed_file"


class ResumeService:
    """Service for resume operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3 = S3Service()

    async def list_resumes(self, user_id: UUID) -> List[ResumeResponse]:
        """List all resumes for a user."""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.is_active == True)
            .order_by(Resume.created_at.desc())
        )
        resumes = result.scalars().all()
        return [self._to_response(r) for r in resumes]

    async def get_resume(self, user_id: UUID, resume_id: UUID) -> ResumeResponse:
        """Get a specific resume."""
        resume = await self._get_user_resume(user_id, resume_id)
        return self._to_response(resume)

    async def upload_resume(
        self,
        user_id: UUID,
        file: UploadFile,
        title: str,
        is_default: bool = False,
    ) -> ResumeResponse:
        """Upload and store a new resume."""
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Unsupported file type: {file.content_type}. "
                f"Allowed: PDF, DOCX, DOC, TXT"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValidationError("File size exceeds 10 MB limit")

        # Sanitize the filename before using it
        safe_filename = _sanitize_filename(file.filename or "unnamed_file")

        # Upload to S3 / local storage
        file_key = f"resumes/{user_id}/{safe_filename}"
        file_url = await self.s3.upload_file(
            file_content=content,
            key=file_key,
            content_type=file.content_type,
        )

        # If setting as primary, unset other primaries
        if is_default:
            await self.db.execute(
                update(Resume)
                .where(Resume.user_id == user_id, Resume.is_primary == True)
                .values(is_primary=False)
            )

        resume = Resume(
            user_id=user_id,
            title=title,
            file_name=safe_filename,
            file_path=file_url,
            file_size=len(content),
            file_type=file.content_type,
            is_primary=is_default,
        )
        self.db.add(resume)
        await self.db.flush()
        await self.db.refresh(resume)

        return self._to_response(resume)

    async def update_resume(
        self, user_id: UUID, resume_id: UUID, data: ResumeUpdate
    ) -> ResumeResponse:
        """Update resume metadata."""
        resume = await self._get_user_resume(user_id, resume_id)

        update_data = data.model_dump(exclude_unset=True)

        # Handle is_default -> is_primary mapping
        if "is_default" in update_data:
            is_default = update_data.pop("is_default")
            if is_default:
                await self.db.execute(
                    update(Resume)
                    .where(Resume.user_id == user_id, Resume.is_primary == True)
                    .values(is_primary=False)
                )
            resume.is_primary = is_default

        if "title" in update_data:
            resume.title = update_data["title"]

        await self.db.flush()
        await self.db.refresh(resume)

        return self._to_response(resume)

    async def download_resume(
        self, user_id: UUID, resume_id: UUID
    ) -> tuple[bytes, str, str]:
        """Download a resume file. Returns (content, filename, content_type)."""
        resume = await self._get_user_resume(user_id, resume_id)
        file_key = f"resumes/{user_id}/{resume.file_name}"
        file_content = await self.s3.download_file(file_key)

        if not file_content:
            raise NotFoundError("Resume file not found in storage")

        return (
            file_content,
            resume.file_name or "resume",
            resume.file_type or "application/octet-stream",
        )

    async def delete_resume(self, user_id: UUID, resume_id: UUID) -> bool:
        """Soft-delete a resume."""
        resume = await self._get_user_resume(user_id, resume_id)

        # Delete file from storage
        if resume.file_path:
            file_key = f"resumes/{user_id}/{resume.file_name}"
            await self.s3.delete_file(file_key)

        resume.is_active = False
        await self.db.flush()

        return True

    async def parse_resume(self, user_id: UUID, resume_id: UUID) -> ResumeParseResponse:
        """Parse a resume and extract structured data."""
        resume = await self._get_user_resume(user_id, resume_id)

        # Download file from storage
        file_key = f"resumes/{user_id}/{resume.file_name}"
        file_content = await self.s3.download_file(file_key)

        if not file_content:
            raise ValidationError("Could not retrieve resume file")

        # Extract text
        mime_type = resume.file_type or "application/pdf"
        text = await ResumeParser.extract_text(file_content, mime_type)
        sections = ResumeParser.parse_sections(text)
        skills = ResumeParser.extract_skills_list(text)

        # Update resume with parsed content
        resume.raw_text = text
        resume.parsed_data = sections
        resume.extracted_skills = skills
        resume.last_parsed_at = datetime.now(timezone.utc)
        await self.db.flush()

        return ResumeParseResponse(
            id=resume.id,
            is_parsed=True,
            parsed_content=sections,
            skills_extracted=skills,
        )

    async def _get_user_resume(self, user_id: UUID, resume_id: UUID) -> Resume:
        """Get resume belonging to user."""
        result = await self.db.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
                Resume.is_active == True,
            )
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise NotFoundError("Resume")
        return resume

    def _to_response(self, resume: Resume) -> ResumeResponse:
        """Convert Resume model to response schema."""
        return ResumeResponse(
            id=resume.id,
            user_id=resume.user_id,
            title=resume.title,
            file_name=resume.file_name or "",
            file_url=resume.file_path or "",
            file_size=resume.file_size or 0,
            mime_type=resume.file_type or "",
            is_default=resume.is_primary,
            is_parsed=resume.last_parsed_at is not None,
            parsed_content=resume.parsed_data,
            created_at=resume.created_at,
            updated_at=resume.updated_at,
        )
