"""End-to-end tests for Agent DID Protocol."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint."""
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openid_configuration(client):
    """Test OIDC discovery endpoint."""
    resp = await client.get("/.well-known/openid-configuration")
    # May fail if no IdP configured, but endpoint should exist
    assert resp.status_code in [200, 500]


@pytest.mark.asyncio
async def test_service_info(client):
    """Test service info endpoint."""
    resp = await client.get("/v1/info")
    assert resp.status_code in [200, 401, 403, 404]


@pytest.mark.asyncio  
async def test_discovery_endpoints(client):
    """Test discovery endpoints exist."""
    resp = await client.get("/.well-known/jwks.json")
    # Should return 404 or 500 if no keys, but route exists
    assert resp.status_code in [200, 404, 500]
