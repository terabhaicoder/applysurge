"""
Job preferences schemas.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobPreferencesUpdate(BaseModel):
    """Schema for updating job preferences."""
    desired_titles: Optional[List[str]] = None
    desired_locations: Optional[List[str]] = None
    remote_preference: Optional[str] = Field(None, pattern="^(remote|hybrid|onsite|any)$")
    min_salary: Optional[int] = Field(None, ge=0)
    max_salary: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    job_types: Optional[List[str]] = None  # full-time, part-time, contract, etc.
    experience_levels: Optional[List[str]] = None  # entry, mid, senior, etc.
    industries: Optional[List[str]] = None
    company_sizes: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    required_keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    willing_to_relocate: Optional[bool] = None
    visa_sponsorship_required: Optional[bool] = None
    min_match_score: Optional[int] = Field(None, ge=0, le=100)


class JobPreferencesResponse(BaseModel):
    """Schema for job preferences response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    desired_titles: Optional[List[str]] = []
    desired_locations: Optional[List[str]] = []
    remote_preference: str = "any"
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    salary_currency: str = "USD"
    job_types: Optional[List[str]] = []
    experience_levels: Optional[List[str]] = []
    industries: Optional[List[str]] = []
    company_sizes: Optional[List[str]] = []
    excluded_companies: Optional[List[str]] = []
    required_keywords: Optional[List[str]] = []
    excluded_keywords: Optional[List[str]] = []
    willing_to_relocate: bool = False
    visa_sponsorship_required: bool = False
    min_match_score: int = 70

    @model_validator(mode="before")
    @classmethod
    def map_model_fields(cls, data):
        """Map database model fields to response schema fields."""
        if hasattr(data, "__dict__"):
            # ORM model object - extract attributes
            obj = data
            result = {
                "id": obj.id,
                "user_id": obj.user_id,
                "desired_titles": obj.desired_titles or [],
                "desired_locations": obj.preferred_locations or [],
                "min_salary": obj.min_salary,
                "max_salary": obj.max_salary,
                "salary_currency": obj.salary_currency or "USD",
                "job_types": obj.job_types or [],
                "experience_levels": obj.experience_levels or [],
                "industries": obj.industries or [],
                "company_sizes": obj.preferred_company_sizes or [],
                "excluded_companies": obj.excluded_companies or [],
                "required_keywords": obj.included_keywords or [],
                "excluded_keywords": obj.excluded_keywords or [],
                "willing_to_relocate": False,
                "visa_sponsorship_required": getattr(obj, "visa_sponsorship_required", False),
                "min_match_score": getattr(obj, "min_match_score", 70),
            }
            # Derive remote_preference from remote_only/hybrid_ok
            ro = getattr(obj, "remote_only", False)
            ho = getattr(obj, "hybrid_ok", False)
            if ro and ho:
                result["remote_preference"] = "any"
            elif ro:
                result["remote_preference"] = "remote"
            elif ho:
                result["remote_preference"] = "hybrid"
            else:
                result["remote_preference"] = "onsite"
            return result

        # Dict input - just coerce None lists to empty
        if isinstance(data, dict):
            list_fields = [
                "desired_titles", "desired_locations", "job_types",
                "experience_levels", "industries", "company_sizes",
                "excluded_companies", "required_keywords", "excluded_keywords",
            ]
            for f in list_fields:
                if f in data and data[f] is None:
                    data[f] = []
        return data
