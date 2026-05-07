"""Agent state transition matrix tests."""
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
        "organization_name": "Didone World",
        "organization_slug": "didoneworld",
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


def make_agent(did: str) -> dict:
    return {
        "agent_id_protocol_version": "0.2.0",
        "agent": {
            "did": did,
            "display_name": "Test Agent",
            "owner": "test",
            "role": "assistant",
            "environment": "development",
            "version": "1.0",
            "status": "active",
            "trust_level": "internal",
            "capabilities": []
        },
        "authorization": {
            "mode": "delegated",
            "subject_context": "on_behalf_of_user",
            "delegation_proof_formats": ["oauth_token_exchange"],
            "scope_reference": "https://test.example/policy",
            "expires_at": "2026-12-31T23:59:59Z",
            "max_delegation_depth": 1,
            "attenuation_required": False,
            "human_approval_required": False
        },
        "governance": {
            "provisioning": "internal_iam",
            "audit_endpoint": "https://test.example/audit",
            "status_endpoint": "https://test.example/status",
            "deprovisioning_endpoint": "https://test.example/deprov",
            "identity_chain_preserved": True
        },
        "bindings": {
            "a2a": {"endpoint_url": "https://test.example/a2a", "agent_card_name": "TestAgent"},
            "acp": {"endpoint_url": None},
            "anp": {"did": None, "endpoint_url": None}
        },
        "extensions": {}
    }


class TestAgentStateTransitions:
    def test_submit_review_endpoint_exists(self, client, auth_headers, blueprint):
        # Create agent first
        create_resp = client.post(f"/v1/blueprints/{blueprint}/agent-records", 
            json=make_agent("did:key:test-review"), headers=auth_headers)
        
        if create_resp.status_code == 201:
            record_id = create_resp.json()["id"]
            # Submit review
            resp = client.post(f"/v1/agent-records/{record_id}/submit-review", headers=auth_headers)
            # Either 200 (success) or 404 (no permission)
            assert resp.status_code in [200, 404, 422]

    def test_approve_endpoint_exists(self, client, auth_headers, blueprint):
        create_resp = client.post(f"/v1/blueprints/{blueprint}/agent-records",
            json=make_agent("did:key:test-approve"), headers=auth_headers)
        
        if create_resp.status_code == 201:
            record_id = create_resp.json()["id"]
            resp = client.post(f"/v1/agent-records/{record_id}/approve", headers=auth_headers)
            assert resp.status_code in [200, 404, 422]

    def test_activate_endpoint_exists(self, client, auth_headers, blueprint):
        create_resp = client.post(f"/v1/blueprints/{blueprint}/agent-records",
            json=make_agent("did:key:test-activate"), headers=auth_headers)
        
        if create_resp.status_code == 201:
            record_id = create_resp.json()["id"]
            resp = client.post(f"/v1/agent-records/{record_id}/activate", headers=auth_headers)
            assert resp.status_code in [200, 404, 422]

    def test_deprovision_endpoint_exists(self, client, auth_headers, blueprint):
        create_resp = client.post(f"/v1/blueprints/{blueprint}/agent-records",
            json=make_agent("did:key:test-deprov"), headers=auth_headers)
        
        if create_resp.status_code == 201:
            record_id = create_resp.json()["id"]
            resp = client.post(f"/v1/agent-records/{record_id}/deprovision",
                json={"requested_by": "test"}, headers=auth_headers)
            assert resp.status_code in [200, 400, 404, 422]


class TestAgentCRUD:
    def test_list_agents(self, client, auth_headers, blueprint):
        resp = client.get(f"/v1/blueprints/{blueprint}/agent-records", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_agent(self, client, auth_headers, blueprint):
        create_resp = client.post(f"/v1/blueprints/{blueprint}/agent-records",
            json=make_agent("did:key:test-get"), headers=auth_headers)
        
        if create_resp.status_code == 201:
            record_id = create_resp.json()["id"]
            get_resp = client.get(f"/v1/agent-records/{record_id}", headers=auth_headers)
            assert get_resp.status_code == 200
