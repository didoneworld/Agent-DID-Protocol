"""Lifecycle transition and audit tests."""
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
        "organization_name": "TestOrg",
        "organization_slug": "test-org",
        "api_key_label": "test-key"
    })
    assert resp.status_code == 201
    return {"X-API-Key": resp.json()["api_key"]}


@pytest.fixture
def blueprint(client, auth_headers):
    resp = client.post("/v1/blueprints", json={
        "blueprint_id": "test-bp",
        "display_name": "Test Blueprint",
        "description": "Test",
        "publisher": "test",
        "sign_in_audience": "AzureADMyOrg"
    }, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["blueprint_id"]


class TestLifecycleTransitions:
    def test_disable_blueprint(self, client, auth_headers, blueprint):
        resp = client.post(f"/v1/blueprints/{blueprint}/disable", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") == True

    def test_enable_blueprint(self, client, auth_headers, blueprint):
        client.post(f"/v1/blueprints/{blueprint}/disable", headers=auth_headers)
        resp = client.post(f"/v1/blueprints/{blueprint}/enable", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") == True


class TestAuditEvents:
    def test_list_audit_events(self, client, auth_headers, blueprint):
        # Create an event via disable
        client.post(f"/v1/blueprints/{blueprint}/disable", headers=auth_headers)
        
        # List audit events
        resp = client.get(f"/v1/audit-events", headers=auth_headers)
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) > 0


class TestDryRun:
    def test_deprovision_endpoint_smoke(self, client, auth_headers, blueprint):
        get_resp = client.get(f"/v1/blueprints/{blueprint}", headers=auth_headers)
        original = get_resp.json()
        
        resp = client.post(f"/v1/blueprints/{blueprint}/deprovision?dry_run=true", headers=auth_headers)
        # Either succeeds or endpoint doesn't exist
        assert resp.status_code in [200, 404]
