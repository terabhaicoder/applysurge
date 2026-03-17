"""
Analytics schemas.
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AnalyticsOverview(BaseModel):
    """Schema for analytics overview."""
    total_applications: int = 0
    applications_this_week: int = 0
    applications_this_month: int = 0
    response_rate: float = 0.0
    interview_rate: float = 0.0
    offer_rate: float = 0.0
    avg_response_time_days: Optional[float] = None
    active_applications: int = 0
    jobs_in_queue: int = 0


class ApplicationAnalytics(BaseModel):
    """Schema for application analytics."""
    total: int = 0
    by_status: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_company: List[dict] = []
    avg_time_to_response: Optional[float] = None


class ResponseAnalytics(BaseModel):
    """Schema for response analytics."""
    total_responses: int = 0
    positive_responses: int = 0
    negative_responses: int = 0
    pending: int = 0
    response_rate: float = 0.0
    avg_days_to_response: Optional[float] = None
    by_company_size: dict[str, float] = {}


class SourceAnalytics(BaseModel):
    """Schema for source analytics."""
    sources: List[dict] = []
    most_effective_source: Optional[str] = None
    by_response_rate: dict[str, float] = {}


class DailyAnalytics(BaseModel):
    """Schema for daily analytics data point."""
    date: date
    applications: int = 0
    responses: int = 0
    interviews: int = 0
    offers: int = 0


class DailyAnalyticsResponse(BaseModel):
    """Schema for daily analytics response."""
    data: List[DailyAnalytics] = []
    period_start: date
    period_end: date
    total_applications: int = 0
    total_responses: int = 0
