"""
Profile management endpoints including education, experience, skills, and certifications.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.profile import (
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
    SkillCreate,
    SkillResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter()


# Profile CRUD
@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's profile with all related data."""
    service = ProfileService(db)
    return await service.get_profile(current_user.id)


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update the user's profile."""
    service = ProfileService(db)
    return await service.create_profile(current_user.id, data)


@router.patch("/", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's profile."""
    service = ProfileService(db)
    return await service.update_profile(current_user.id, data)


@router.delete("/", response_model=MessageResponse)
async def delete_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the user's profile."""
    service = ProfileService(db)
    await service.delete_profile(current_user.id)
    return MessageResponse(message="Profile deleted")


# Education
@router.post(
    "/education",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_education(
    data: EducationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an education entry."""
    service = ProfileService(db)
    return await service.add_education(current_user.id, data)


@router.patch("/education/{education_id}", response_model=EducationResponse)
async def update_education(
    education_id: UUID,
    data: EducationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an education entry."""
    service = ProfileService(db)
    return await service.update_education(current_user.id, education_id, data)


@router.delete("/education/{education_id}", response_model=MessageResponse)
async def delete_education(
    education_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an education entry."""
    service = ProfileService(db)
    await service.delete_education(current_user.id, education_id)
    return MessageResponse(message="Education entry deleted")


# Experience
@router.post(
    "/experience",
    response_model=ExperienceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_experience(
    data: ExperienceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an experience entry."""
    service = ProfileService(db)
    return await service.add_experience(current_user.id, data)


@router.patch("/experience/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: UUID,
    data: ExperienceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an experience entry."""
    service = ProfileService(db)
    return await service.update_experience(current_user.id, experience_id, data)


@router.delete("/experience/{experience_id}", response_model=MessageResponse)
async def delete_experience(
    experience_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an experience entry."""
    service = ProfileService(db)
    await service.delete_experience(current_user.id, experience_id)
    return MessageResponse(message="Experience entry deleted")


# Skills
@router.get("/skills", response_model=list[SkillResponse])
async def get_skills(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all skills."""
    service = ProfileService(db)
    return await service.get_skills(current_user.id)


@router.post(
    "/skills",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_skill(
    data: SkillCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a skill."""
    service = ProfileService(db)
    return await service.add_skill(current_user.id, data)


@router.delete("/skills/{skill_id}", response_model=MessageResponse)
async def delete_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a skill."""
    service = ProfileService(db)
    await service.delete_skill(current_user.id, skill_id)
    return MessageResponse(message="Skill deleted")


# Certifications
@router.post(
    "/certifications",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_certification(
    data: CertificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a certification."""
    service = ProfileService(db)
    return await service.add_certification(current_user.id, data)


@router.patch("/certifications/{certification_id}", response_model=CertificationResponse)
async def update_certification(
    certification_id: UUID,
    data: CertificationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a certification."""
    service = ProfileService(db)
    return await service.update_certification(current_user.id, certification_id, data)


@router.delete("/certifications/{certification_id}", response_model=MessageResponse)
async def delete_certification(
    certification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a certification."""
    service = ProfileService(db)
    await service.delete_certification(current_user.id, certification_id)
    return MessageResponse(message="Certification deleted")
