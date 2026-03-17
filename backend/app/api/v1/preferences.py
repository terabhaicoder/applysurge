"""
Job preferences endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.preferences import JobPreferences
from app.schemas.preferences import JobPreferencesResponse, JobPreferencesUpdate

router = APIRouter()


@router.get("/", response_model=JobPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's job preferences."""
    result = await db.execute(
        select(JobPreferences).where(JobPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = JobPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)

    return JobPreferencesResponse.model_validate(prefs)


@router.put("/", response_model=JobPreferencesResponse)
async def update_preferences(
    data: JobPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's job preferences."""
    result = await db.execute(
        select(JobPreferences).where(JobPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = JobPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)

    update_data = data.model_dump(exclude_unset=True)

    # Map schema field names to model field names
    field_mapping = {
        "desired_locations": "preferred_locations",
        "company_sizes": "preferred_company_sizes",
        "required_keywords": "included_keywords",
    }

    for schema_field, value in update_data.items():
        if schema_field == "remote_preference":
            # Convert remote_preference string to model booleans
            prefs.remote_only = value in ("remote", "any")
            prefs.hybrid_ok = value in ("hybrid", "any")
        else:
            model_field = field_mapping.get(schema_field, schema_field)
            if hasattr(prefs, model_field):
                setattr(prefs, model_field, value)

    await db.flush()
    await db.refresh(prefs)

    return JobPreferencesResponse.model_validate(prefs)
