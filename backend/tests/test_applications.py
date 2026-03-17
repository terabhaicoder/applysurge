"""Application endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job


@pytest.mark.asyncio
async def test_list_applications_empty(client: AsyncClient, auth_headers: dict):
    """Test listing applications when none exist."""
    response = await client.get("/api/v1/applications/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_applications(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user
):
    """Test listing applications with data."""
    job = Job(
        source="linkedin",
        source_job_id="app_test_job",
        source_url="https://linkedin.com/jobs/789",
        title="Full Stack Developer",
        company_name="BigCorp",
        location="NYC",
        description="Description",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    app = Application(
        user_id=test_user.id,
        job_id=job.id,
        job_title="Full Stack Developer",
        company_name="BigCorp",
        application_method="linkedin_easy_apply",
        status="applied",
    )
    db_session.add(app)
    await db_session.commit()

    response = await client.get("/api/v1/applications/", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_application_stats(client: AsyncClient, auth_headers: dict):
    """Test getting application statistics."""
    response = await client.get("/api/v1/applications/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data


@pytest.mark.asyncio
async def test_update_application_status(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user
):
    """Test updating application status."""
    job = Job(
        source="naukri",
        source_job_id="status_test",
        source_url="https://naukri.com/job/status",
        title="DevOps Engineer",
        company_name="CloudCo",
        location="Remote",
        description="Description",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    app = Application(
        user_id=test_user.id,
        job_id=job.id,
        job_title="DevOps Engineer",
        company_name="CloudCo",
        application_method="naukri_apply",
        status="applied",
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)

    response = await client.patch(
        f"/api/v1/applications/{app.id}/status",
        headers=auth_headers,
        json={"status": "interview_scheduled"},
    )
    assert response.status_code == 200
