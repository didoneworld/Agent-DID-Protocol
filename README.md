# Agent DID

> **Status:** Stable MVP / reference implementation. Ready for continued development and internal evaluation. **Not production ready yet.**

Open source, vendor-agnostic agent identity and access management control plane built around OpenID Connect, SAML, SCIM, Shared Signals, W3C Decentralized Identifiers, and Agent Identity Blueprints.

Agent DID defines an Agent ID record format and provides a runnable FastAPI reference implementation for managing agent identities, governance metadata, authorization, lifecycle operations, blueprint-backed identity fleets, and enterprise identity integrations.

## Current status

Agent DID is now stable enough for continued feature development and internal evaluation. The runtime/import/schema blockers around Agent Identity Blueprints were fixed in PR #8 and merged into `main`.

Current readiness:

| Area | Status |
|---|---|
| Local development | Ready |
| Internal evaluation | Ready |
| Blueprint feature development | Ready |
| Production enterprise deployment | Not ready |
| Security/compliance hardening | In progress |
| Production observability | Not complete |
| Full OIDC/SAML hardening | Not complete |

Merged stabilization work includes:

- fixed blueprint model imports in `app/main.py`
- added missing `PermissionGrant` schema
- aligned blueprint response fields with schema field names
- replaced `blueprint.credentials` relationship access with direct credential queries
- fixed owner/sponsor field handling
- added production startup validation for `SESSION_SIGNING_SECRET`
- improved API key hashing with HMAC-SHA256 pepper support
- added Redis-backed rate limiter support for production deployments when `REDIS_URL` is set
- added Gunicorn production startup with `uvicorn.workers.UvicornWorker`
- fixed Docker smoke-test port mapping
- added CI workflow for tests, linting, Docker build, and smoke test
- added initial E2E smoke tests

Merge commit:

```text
3b54c9d8dc6c63543fc466327697c4cbfa22fd76
```

Agent DID is still not a fully hardened enterprise identity platform. Treat it as a serious MVP/reference implementation until the production-readiness checklist below is complete.

## What this repository contains

This repository includes both the Agent ID protocol draft and a working SaaS-style control plane.

### Protocol and interoperability

- Agent ID protocol draft
- DID-backed agent identity records
- Agent Identity Blueprint alignment model
- Governance and lifecycle metadata for long-running agents
- Authorization metadata for delegated and autonomous agent operation
- Protocol binding examples for A2A, ACP, and ANP
- JSON Schema for validating Agent ID records
- Compatibility and publication guidance

Agent DID does not define agent-to-agent messaging. It is designed to work alongside interoperability protocols such as A2A, ACP, ANP, MCP, OpenAPI, and other agent communication standards.

### Control plane

The FastAPI application provides a tenant-scoped registry and admin surface for Agent ID records and blueprint-backed agent identity fleets.

Current capabilities include:

- tenant bootstrap with first admin API key
- API key authentication with `X-API-Key`
- bearer session authentication
- admin, writer, and reader roles
- OIDC and SAML identity provider configuration
- OIDC discovery and SSO routes
- SAML ACS support
- SCIM lifecycle endpoints
- Shared Signals Framework routes
- approval workflow routes
- database-backed Agent ID registry
- Agent Identity Blueprint CRUD routes
- blueprint child-agent inventory and creation routes
- blueprint credential creation, rotation, and deletion routes
- blueprint principal routes
- blueprint permission preview and revoke routes
- record-level fine-grained authorization tuples
- audit logging for identity and lifecycle events
- deprovisioning support
- schema revision tracking and startup migrations
- in-memory request rate limiting for local development
- Redis-backed rate limiting for production when configured
- request ID logging
- SQLite for local development
- `DATABASE_URL` support for Postgres deployments
- built-in web admin console at `/`
- Docker and Gunicorn production startup support
- GitHub Actions CI for tests, lint, Docker build, and smoke test

## Repository layout

```text
app/                          FastAPI SaaS control plane
app/routers/                  OIDC, SAML, SCIM, session, and discovery routers
app/static/                   Built-in admin console assets
alembic.ini                   Alembic configuration
docs/agent-id-spec.md         Agent ID protocol draft
docs/product-documentation.md Product behavior, configuration, defaults, and API docs
docs/openid-alignment.md      Rationale for OpenID authorization and governance alignment
docs/compatibility.md         Evolution and compatibility rules
docs/lifecycle-management.md  Lifecycle states, policies, workflows, and runbooks
schemas/agent-id-record.yaml  Core Agent ID record example
schemas/json/                 JSON Schemas
examples/                     Protocol binding and DID method examples
templates/publish-checklist.md Publication checklist
tests/                        Automated test suite
scripts/                      Validation and utility scripts
sdk/python/                   Python SDK
.github/workflows/            CI/CD workflows
```

## Quick start

### Run locally with Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

Open the admin console:

```text
http://127.0.0.1:8000/
```

Check service health:

```bash
curl http://127.0.0.1:8000/health
```

Bootstrap the first organization and admin API key:

```bash
curl -X POST http://127.0.0.1:8000/v1/bootstrap \
  -H 'content-type: application/json' \
  -d '{"organization_name":"Didone World","organization_slug":"didoneworld","api_key_label":"ops-admin"}'
```

The bootstrap response returns the first admin API key. Store it securely; it is used with the `X-API-Key` header for authenticated API calls.

## Run with Docker

Build and run locally:

```bash
docker build -t agent-identity:local .
docker run --rm -p 8000:8000 agent-identity:local
```

Run validation inside the image:

```bash
docker run --rm agent-identity:local /app/scripts/validate.sh
```

Production-style startup uses Gunicorn with Uvicorn workers when `ENV=production`:

```bash
docker run --rm \
  -e ENV=production \
  -e SESSION_SIGNING_SECRET='replace-with-a-strong-secret' \
  -p 8000:8000 \
  agent-identity:local
```

Use Redis-backed rate limiting in production by setting `REDIS_URL`:

```bash
docker run --rm \
  -e ENV=production \
  -e SESSION_SIGNING_SECRET='replace-with-a-strong-secret' \
  -e REDIS_URL='redis://redis:6379' \
  -p 8000:8000 \
  agent-identity:local
```

Published images:

- Docker Hub: `autonomyx/agent-identity:latest`
- GHCR: `ghcr.io/didoneworld/agent-identity:latest`

## Run with Docker Compose

Start the app with Postgres:

```bash
docker compose up --build
```

The compose stack exposes:

- app: `http://127.0.0.1:8000`
- database: `postgresql://agentid:agentid@127.0.0.1:5432/agentid`

Use alternate host ports when defaults are already taken:

```bash
APP_PORT=8012 POSTGRES_PORT=5433 docker compose up --build
```

Create a local environment file from the template:

```bash
cp .env.example .env
```

## Agent Identity Blueprint Alignment

Agent DID supports a vendor-neutral **Agent Identity Blueprint** model inspired by Microsoft Entra Agent ID blueprints. A blueprint is a reusable template and policy container for many DID-backed child agent identities.

A blueprint captures:

- publisher metadata
- sign-in audience
- identifier URIs
- app roles
- optional claims
- credential policy
- required resource access
- inheritable permissions
- owners
- sponsors
- tenant-local blueprint principals
- lifecycle policy actions

Blueprint-backed records remain compatible with A2A, ACP, and ANP because the child Agent ID record still owns protocol bindings and `agent.did`. Microsoft Entra compatibility is provided as an alignment profile rather than a hard dependency; non-Microsoft providers can use `extension_fields` for local issuer, federation, principal, and managed identity metadata.

Existing Agent ID records are backward compatible. `blueprint_id` is optional, so standalone records continue to validate. To migrate, create a blueprint for shared metadata and permissions, then upsert each child Agent ID record with `blueprint_id` at the top level or in `extensions.blueprint_id`.

Blueprint APIs include CRUD routes, child record creation and inventory, effective permission preview, credential creation/rotation/deletion, and policy actions for disable, enable, quarantine, deprovision, and export.

See [`docs/entra-blueprint-alignment.md`](docs/entra-blueprint-alignment.md) for token-flow alignment and migration guidance.

## Core API surface

Unauthenticated:

- `GET /health`
- `GET /`
- `POST /v1/bootstrap`
- `GET /.well-known/*`
- `GET /v1/sso/oidc/start/{organization_slug}`
- `POST /v1/sso/oidc/callback/{organization_slug}`
- `POST /v1/sso/saml/acs/{organization_slug}`

Authenticated with API key or bearer session:

- `GET /v1/organizations`
- `GET /v1/identity-providers`
- `GET /v1/agent-records`
- `POST /v1/agent-records`
- `GET /v1/agent-records/{record_id}`
- `GET /v1/agent-records/by-did/{did}`
- `POST /v1/agent-records/{record_id}/deprovision`
- `GET /v1/blueprints`
- `POST /v1/blueprints`
- `GET /v1/blueprints/{blueprint_id}`
- `PATCH /v1/blueprints/{blueprint_id}`
- `DELETE /v1/blueprints/{blueprint_id}`
- `POST /v1/blueprints/{blueprint_id}/disable`
- `POST /v1/blueprints/{blueprint_id}/enable`
- `GET /v1/blueprints/{blueprint_id}/agent-records`
- `POST /v1/blueprints/{blueprint_id}/agent-records`
- `GET /v1/blueprints/{blueprint_id}/permissions/effective`
- `POST /v1/blueprints/{blueprint_id}/permissions/revoke`
- `POST /v1/blueprints/{blueprint_id}/principals`
- `DELETE /v1/blueprints/{blueprint_id}/principals/{principal_id}`
- `POST /v1/blueprints/{blueprint_id}/credentials`
- `POST /v1/blueprints/{blueprint_id}/credentials/{credential_id}/rotate`
- `DELETE /v1/blueprints/{blueprint_id}/credentials/{credential_id}`
- `GET /v1/audit-events`
- `GET /v1/fga/tuples`
- `POST /v1/fga/tuples`
- `POST /v1/fga/check`
- `GET /v1/scim/v2/*`
- `POST /v1/ssf/*`
- `GET /v1/approvals/*`

Admin API key only:

- `GET /v1/api-keys`
- `POST /v1/api-keys`
- `POST /v1/api-keys/{api_key_id}/revoke`
- `POST /v1/identity-providers/oidc`
- `POST /v1/identity-providers/saml`

Interactive OpenAPI documentation is available from FastAPI at:

```text
http://127.0.0.1:8000/docs
```

## Identity model

Agent DID separates identity, authorization, governance, and lifecycle:

- DIDs identify agents.
- Agent ID records describe agent capabilities, bindings, governance, and authorization metadata.
- Agent Identity Blueprints define reusable metadata, credential, permission, owner, sponsor, and policy templates.
- Authorization metadata describes whether agents act autonomously or on behalf of users, teams, or systems.
- Governance metadata exposes lifecycle, audit, approval, and deprovisioning controls for long-running agents.

Recommended DID methods:

- `did:web` for public organization-managed agent identities
- `did:key` for local, ephemeral, or lightweight agent identities

Examples:

- `examples/did-methods/did-web-agent.yaml`
- `examples/did-methods/did-key-agent.yaml`

## Lifecycle management

Agent DID includes explicit, policy-governed lifecycle management for Agent ID records and Agent Identity Blueprints.

Highlights:

- lifecycle states and transition validation for agents and blueprints
- lifecycle APIs for review, approval, activation, suspension, resumption, quarantine, renewal, credential rotation, deprovisioning, archive, and delete
- activation validation gates for DID documents, verification methods, credentials, permissions, sponsors, owners, governance endpoints, audit logging, production hardening, risk thresholds, and quarantine/revocation status
- staged, idempotent, auditable deprovisioning with dry-run reports and blueprint child cascade support
- lifecycle audit event queries, webhook event schemas, policy schemas, renewal/risk/quarantine models, and operational runbooks
- backward-compatible migration semantics for records without lifecycle state

See [`docs/lifecycle-management.md`](docs/lifecycle-management.md) for state diagrams, policy configuration, workflows, APIs, examples, and migration guidance.

## SDKs

A Python SDK is available in [`sdk/python`](sdk/python/README.md) for adopters who want to integrate Agent DID lifecycle operations into their own portals, workers, CI/CD automations, or identity governance systems. It supports API-key, bearer-token, and dynamic auth-provider adapters while keeping Agent DID lifecycle operations vendor-neutral.

## CI/CD

GitHub Actions is configured to:

- run tests on pull requests
- run linting with Ruff
- build and smoke test the container on pull requests
- publish image tags on `main` pushes and `v*` tags when publishing workflows are configured

Required GitHub repository secrets for Docker Hub publishing:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

GHCR publishing uses `GITHUB_TOKEN` with package write permission.

## Current limitations

Agent DID is a serious MVP and reference SaaS foundation, not a fully hardened enterprise identity platform.

Known limitations include:

- external OIDC production hardening still needs full authorization-code exchange, ID-token validation, nonce/state validation, JWKS validation, and provider-specific claim mapping
- SAML metadata ingestion, signed assertion validation, certificate validation, logout, and full SP hardening are not complete
- internal FGA is intentionally minimal and is not OpenFGA-compatible yet
- admin UI does not yet expose every API capability
- SCIM, SSF, approvals, and lifecycle automation are early product slices
- Redis rate limiting exists, but production operations need Redis health checks, fail-closed/fail-open policy controls, and multi-instance tests
- Alembic configuration exists, but full versioned migration scripts, rollback testing, and deployment migration runbooks still need to mature
- webhook delivery exists as an async helper, but durable queues, dead-letter handling, replay, and operational dashboards are still future work
- secret encryption at rest for identity provider credentials and other sensitive fields still needs to be implemented
- blueprint endpoint coverage is still thin and should be expanded beyond smoke tests

## Production-readiness checklist

Before using Agent DID in production, complete and verify:

- full OIDC authorization-code flow validation
- production-grade SAML validation
- encryption at rest for sensitive secrets
- versioned Alembic migrations and rollback tests
- distributed rate-limit tests with Redis
- durable background workers for lifecycle, webhook, rotation, and deprovisioning jobs
- blueprint CRUD, credential, permission, and effective-permission endpoint tests
- tenant isolation tests
- security and abuse tests
- structured logs, metrics, traces, alerts, and audit export
- production deployment manifests
- backup and restore procedures
- license selection
- security disclosure process

## Roadmap

Planned work includes:

1. Harden OIDC and SAML flows with full token validation, signed metadata, logout, and session revocation.
2. Expand authorization with group mapping, inheritance, policy templates, and an OpenFGA-compatible model.
3. Mature SCIM, SSF, approvals, audit export, key rotation, and lifecycle automation.
4. Improve operations with complete Alembic migrations, Redis deployment guidance, workers, metrics, tracing, and deployment manifests.
5. Expand the admin console for identity providers, sessions, FGA tuples, teams, tenant settings, blueprints, lifecycle actions, and approvals.
6. Add stronger blueprint endpoint tests and schema validation tests.

## License

Add license information here before using Agent DID in production or redistributing packaged builds.
