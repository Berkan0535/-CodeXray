import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CodeXray" in data["service"]


@pytest.mark.asyncio
async def test_analyze_repository_api_flow(client: AsyncClient):
    # Submit analysis for valid GitHub repo URL
    payload = {
        "repository_url": "https://github.com/pallets/flask",
        "branch": "main"
    }
    response = await client.post("/api/v1/repositories/analyze", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["status"] in ("queued", "running")
    analysis_id = data["id"]

    # Poll status endpoint
    status_resp = await client.get(f"/api/v1/analyses/{analysis_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "stage" in status_data

    # List repositories
    repos_resp = await client.get("/api/v1/repositories")
    assert repos_resp.status_code == 200
    repos = repos_resp.json()
    assert len(repos) >= 1
    assert repos[0]["name"] == "flask"


@pytest.mark.asyncio
async def test_security_blocked_url(client: AsyncClient):
    # Test blocked private IP / SSRF attempt
    payload = {
        "repository_url": "http://127.0.0.1:8000/internal-repo",
    }
    response = await client.post("/api/v1/repositories/analyze", json=payload)
    assert response.status_code == 400
    assert "Security check failed" in response.json()["detail"]
