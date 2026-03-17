"""Job endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


@pytest.mark.asyncio
async def test_list_jobs_unauthorized(client: AsyncClient):
    """Test listing jobs without auth returns 401."""
    response = await client.get("/api/v1/jobs/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_jobs_empty(client: AsyncClient, auth_headers: dict):
    """Test listing jobs when none exist."""
    response = await client.get("/api/v1/jobs/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_jobs_with_data(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """Test listing jobs with data."""
    # Create test jobs
    for i in range(5):
        job = Job(
            source="linkedin",
            source_job_id=f"job_{i}",
            source_url=f"https://linkedin.com/jobs/{i}",
            title=f"Software Engineer {i}",
            company_name=f"Company {i}",
            location="Remote",
            description=f"Description for job {i}",
        )
        db_session.add(job)
    await db_session.commit()

    response = await client.get("/api/v1/jobs/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_get_job_detail(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """Test getting job details."""
    job = Job(
        source="linkedin",
        source_job_id="detail_job",
        source_url="https://linkedin.com/jobs/123",
        title="Senior Developer",
        company_name="TechCorp",
        location="San Francisco",
        description="Great opportunity",
        salary_min=150000,
        salary_max=200000,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.get(f"/api/v1/jobs/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Senior Developer"
    assert data["company_name"] == "TechCorp"


@pytest.mark.asyncio
async def test_save_job(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    """Test saving/bookmarking a job."""
    job = Job(
        source="naukri",
        source_job_id="save_job",
        source_url="https://naukri.com/job/456",
        title="Backend Developer",
        company_name="StartupXYZ",
        location="Bangalore",
        description="Exciting role",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.post(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_nonexistent_job(client: AsyncClient, auth_headers: dict):
    """Test getting a job that doesn't exist."""
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/jobs/{fake_id}", headers=auth_headers)
    assert response.status_code == 404
