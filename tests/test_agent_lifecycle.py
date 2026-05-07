"""Agent lifecycle transition tests - endpoint availability."""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
import tempfile


@pytest.fixture
def client():
    tmp = tempfile.mkdtemp()
    app = create_app(database_url=f"sqlite:///{tmp}/test.db")
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    resp = client.post("/v1/bootstrap", json={
        "organization_name": "Test",
        "organization_slug": "test",
        "api_key_label": "key"
    })
    assert resp.status_code == 201
    return {"X-API-Key": resp.json()["api_key"]}


@pytest.fixture
def blueprint_id(client, auth_headers):
    resp = client.post("/v1/blueprints", json={
        "blueprint_id": "test-blueprint",
        "display_name": "Test Blueprint",
        "description": "Test",
        "publisher": "test",
        "sign_in_audience": "AzureADMyOrg"
    }, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["blueprint_id"]


class TestBlueprintLifecycle:
    def test_disable_blueprint(self, client, auth_headers, blueprint_id):
        resp = client.post(f"/v1/blueprints/{blueprint_id}/disable", headers=auth_headers)
        assert resp.status_code == 200

    def test_enable_blueprint(self, client, auth_headers, blueprint_id):
        resp = client.post(f"/v1/blueprints/{blueprint_id}/enable", headers=auth_headers)
        assert resp.status_code == 200


class TestAgentRecordEndpoints:
    def test_agent_get(self, client, auth_headers, blueprint_id):
        resp = client.get("/v1/agent-records/nonexistent", headers=auth_headers)
        assert resp.status_code in [200, 404]

    def test_agent_list(self, client, auth_headers, blueprint_id):
        resp = client.get(f"/v1/blueprints/{blueprint_id}/agent-records", headers=auth_headers)
        assert resp.status_code == 200
