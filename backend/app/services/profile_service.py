"""
Profile management service including education, experience, skills, and certifications.
"""

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.profile import (
    UserProfile,
    UserEducation,
    UserExperience,
    UserSkill,
    UserCertification,
)
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    EducationCreate,
    EducationUpdate,
    EducationResponse,
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
    SkillCreate,
    SkillResponse,
    CertificationCreate,
    CertificationUpdate,
    CertificationResponse,
)


class ProfileService:
    """Service for profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: UUID) -> ProfileResponse:
        """Get user profile with all related data."""
        result = await self.db.execute(
            select(UserProfile)
            .where(UserProfile.user_id == user_id)
            .options(
                selectinload(UserProfile.education),
                selectinload(UserProfile.experience),
                selectinload(UserProfile.skills),
                selectinload(UserProfile.certifications),
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
            # Re-fetch with eager loading to avoid lazy-load issues
            result = await self.db.execute(
                select(UserProfile)
                .where(UserProfile.user_id == user_id)
                .options(
                    selectinload(UserProfile.education),
                    selectinload(UserProfile.experience),
                    selectinload(UserProfile.skills),
                    selectinload(UserProfile.certifications),
                )
            )
            profile = result.scalar_one()

        return ProfileResponse.model_validate(profile)

    async def create_profile(self, user_id: UUID, data: ProfileCreate) -> ProfileResponse:
        """Create or update user profile."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
        else:
            profile_data = data.model_dump(exclude_unset=True)
            profile = UserProfile(user_id=user_id, **profile_data)
            self.db.add(profile)

        await self.db.flush()
        await self.db.refresh(profile)
        return await self.get_profile(user_id)

    async def update_profile(self, user_id: UUID, data: ProfileUpdate) -> ProfileResponse:
        """Update user profile."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile_data = data.model_dump(exclude_unset=True)
            profile = UserProfile(user_id=user_id, **profile_data)
            self.db.add(profile)
        else:
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)

        await self.db.flush()
        await self.db.refresh(profile)
        return await self.get_profile(user_id)

    async def delete_profile(self, user_id: UUID) -> bool:
        """Delete user profile."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundError("Profile")

        await self.db.delete(profile)
        await self.db.flush()
        return True

    # Education
    async def add_education(self, user_id: UUID, data: EducationCreate) -> EducationResponse:
        """Add education entry."""
        profile = await self._ensure_profile(user_id)
        education = UserEducation(profile_id=profile.id, **data.model_dump())
        self.db.add(education)
        await self.db.flush()
        await self.db.refresh(education)
        return EducationResponse.model_validate(education)

    async def update_education(
        self, user_id: UUID, education_id: UUID, data: EducationUpdate
    ) -> EducationResponse:
        """Update education entry."""
        education = await self._get_education(user_id, education_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(education, field):
                setattr(education, field, value)
        await self.db.flush()
        await self.db.refresh(education)
        return EducationResponse.model_validate(education)

    async def delete_education(self, user_id: UUID, education_id: UUID) -> bool:
        """Delete education entry."""
        education = await self._get_education(user_id, education_id)
        await self.db.delete(education)
        await self.db.flush()
        return True

    # Experience
    async def add_experience(self, user_id: UUID, data: ExperienceCreate) -> ExperienceResponse:
        """Add experience entry."""
        profile = await self._ensure_profile(user_id)
        experience = UserExperience(profile_id=profile.id, **data.model_dump())
        self.db.add(experience)
        await self.db.flush()
        await self.db.refresh(experience)
        return ExperienceResponse.model_validate(experience)

    async def update_experience(
        self, user_id: UUID, experience_id: UUID, data: ExperienceUpdate
    ) -> ExperienceResponse:
        """Update experience entry."""
        experience = await self._get_experience(user_id, experience_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(experience, field):
                setattr(experience, field, value)
        await self.db.flush()
        await self.db.refresh(experience)
        return ExperienceResponse.model_validate(experience)

    async def delete_experience(self, user_id: UUID, experience_id: UUID) -> bool:
        """Delete experience entry."""
        experience = await self._get_experience(user_id, experience_id)
        await self.db.delete(experience)
        await self.db.flush()
        return True

    # Skills
    async def add_skill(self, user_id: UUID, data: SkillCreate) -> SkillResponse:
        """Add skill."""
        profile = await self._ensure_profile(user_id)
        skill = UserSkill(profile_id=profile.id, **data.model_dump())
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return SkillResponse.model_validate(skill)

    async def delete_skill(self, user_id: UUID, skill_id: UUID) -> bool:
        """Delete skill."""
        profile = await self._ensure_profile(user_id)
        result = await self.db.execute(
            select(UserSkill).where(
                UserSkill.id == skill_id, UserSkill.profile_id == profile.id
            )
        )
        skill = result.scalar_one_or_none()
        if not skill:
            raise NotFoundError("Skill")
        await self.db.delete(skill)
        await self.db.flush()
        return True

    async def get_skills(self, user_id: UUID) -> List[SkillResponse]:
        """Get all skills for a user."""
        profile = await self._ensure_profile(user_id)
        result = await self.db.execute(
            select(UserSkill).where(UserSkill.profile_id == profile.id)
        )
        skills = result.scalars().all()
        return [SkillResponse.model_validate(s) for s in skills]

    # Certifications
    async def add_certification(
        self, user_id: UUID, data: CertificationCreate
    ) -> CertificationResponse:
        """Add certification."""
        profile = await self._ensure_profile(user_id)
        certification = UserCertification(profile_id=profile.id, **data.model_dump())
        self.db.add(certification)
        await self.db.flush()
        await self.db.refresh(certification)
        return CertificationResponse.model_validate(certification)

    async def update_certification(
        self, user_id: UUID, certification_id: UUID, data: CertificationUpdate
    ) -> CertificationResponse:
        """Update certification."""
        certification = await self._get_certification(user_id, certification_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(certification, field):
                setattr(certification, field, value)
        await self.db.flush()
        await self.db.refresh(certification)
        return CertificationResponse.model_validate(certification)

    async def delete_certification(self, user_id: UUID, certification_id: UUID) -> bool:
        """Delete certification."""
        certification = await self._get_certification(user_id, certification_id)
        await self.db.delete(certification)
        await self.db.flush()
        return True

    # Helpers
    async def _ensure_profile(self, user_id: UUID) -> UserProfile:
        """Get or create profile for user."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
        return profile

    async def _get_education(self, user_id: UUID, education_id: UUID) -> UserEducation:
        """Get education entry belonging to user."""
        profile = await self._ensure_profile(user_id)
        result = await self.db.execute(
            select(UserEducation).where(
                UserEducation.id == education_id,
                UserEducation.profile_id == profile.id,
            )
        )
        education = result.scalar_one_or_none()
        if not education:
            raise NotFoundError("Education")
        return education

    async def _get_experience(self, user_id: UUID, experience_id: UUID) -> UserExperience:
        """Get experience entry belonging to user."""
        profile = await self._ensure_profile(user_id)
        result = await self.db.execute(
            select(UserExperience).where(
                UserExperience.id == experience_id,
                UserExperience.profile_id == profile.id,
            )
        )
        experience = result.scalar_one_or_none()
        if not experience:
            raise NotFoundError("Experience")
        return experience

    async def _get_certification(self, user_id: UUID, cert_id: UUID) -> UserCertification:
        """Get certification belonging to user."""
        profile = await self._ensure_profile(user_id)
        result = await self.db.execute(
            select(UserCertification).where(
                UserCertification.id == cert_id,
                UserCertification.profile_id == profile.id,
            )
        )
        cert = result.scalar_one_or_none()
        if not cert:
            raise NotFoundError("Certification")
        return cert
