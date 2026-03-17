"""User endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_profile(client: AsyncClient, auth_headers: dict):
    """Test getting the authenticated user's profile."""
    response = await client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient, auth_headers: dict):
    """Test updating the authenticated user's profile."""
    update_data = {
        "full_name": "Updated User",
        "phone": "+1234567890",
        "location": "San Francisco, CA",
        "bio": "Software engineer with 5 years of experience.",
    }
    response = await client.put(
        "/api/v1/profile",
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated User"
    assert data["phone"] == "+1234567890"
    assert data["location"] == "San Francisco, CA"
    assert data["bio"] == "Software engineer with 5 years of experience."


@pytest.mark.asyncio
async def test_get_user_profile_unauthenticated(client: AsyncClient):
    """Test that accessing profile without auth returns 401."""
    response = await client.get("/api/v1/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, auth_headers: dict):
    """Test changing the user's password."""
    response = await client.post(
        "/api/v1/users/change-password",
        json={
            "old_password": "testpassword123",
            "new_password": "newpassword456",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_user_preferences(client: AsyncClient, auth_headers: dict):
    """Test getting the authenticated user's preferences."""
    response = await client.get("/api/v1/preferences", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_update_user_preferences(client: AsyncClient, auth_headers: dict):
    """Test updating the authenticated user's preferences."""
    preferences_data = {
        "target_titles": ["Software Engineer", "Backend Developer"],
        "target_locations": ["San Francisco", "Remote"],
        "min_salary": 120000,
        "job_types": ["full-time", "contract"],
        "remote_only": False,
    }
    response = await client.put(
        "/api/v1/preferences",
        json=preferences_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["target_titles"] == ["Software Engineer", "Backend Developer"]
    assert data["target_locations"] == ["San Francisco", "Remote"]
    assert data["min_salary"] == 120000
    assert data["job_types"] == ["full-time", "contract"]
    assert data["remote_only"] is False
