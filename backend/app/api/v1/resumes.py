"""
Resume management endpoints.
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.resume import ResumeParseResponse, ResumeResponse, ResumeUpdate
from app.services.resume_service import ResumeService

router = APIRouter()


@router.get("/", response_model=list[ResumeResponse])
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all resumes for the current user."""
    service = ResumeService(db)
    return await service.list_resumes(current_user.id)


@router.post("/", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    title: str = Form(...),
    is_default: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new resume file (PDF, DOCX, DOC, or TXT)."""
    service = ResumeService(db)
    return await service.upload_resume(
        user_id=current_user.id,
        file=file,
        title=title,
        is_default=is_default,
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific resume."""
    service = ResumeService(db)
    return await service.get_resume(current_user.id, resume_id)


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a resume file."""
    service = ResumeService(db)
    content, filename, content_type = await service.download_resume(
        current_user.id, resume_id
    )

    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.patch("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID,
    data: ResumeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update resume metadata (title, default status)."""
    service = ResumeService(db)
    return await service.update_resume(current_user.id, resume_id, data)


@router.delete("/{resume_id}", response_model=MessageResponse)
async def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a resume and its associated file."""
    service = ResumeService(db)
    await service.delete_resume(current_user.id, resume_id)
    return MessageResponse(message="Resume deleted successfully")


@router.post("/{resume_id}/parse", response_model=ResumeParseResponse)
async def parse_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Parse a resume to extract structured data and skills."""
    service = ResumeService(db)
    return await service.parse_resume(current_user.id, resume_id)
