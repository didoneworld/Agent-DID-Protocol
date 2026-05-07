from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings:
    def __init__(self) -> None:
        default_db_path = ROOT_DIR / "data" / "agent_id_protocol.db"
        self.root_dir = ROOT_DIR
        self.service_name = "agent-identity-saas"
        self.app_version = "0.3.0"
        self.database_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")
        self.api_rate_limit_requests = int(os.getenv("API_RATE_LIMIT_REQUESTS", "120"))
        self.api_rate_limit_window_seconds = int(os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", "60"))
        
        # Production secret validation - fail hard if using dev secret in production
        self.env = os.getenv("ENV", "development")
        self.session_signing_secret = os.getenv("SESSION_SIGNING_SECRET", "")
        if not self.session_signing_secret:
            if self.env == "production":
                raise ValueError("SESSION_SIGNING_SECRET must be set in production - cannot use default dev secret")
            self.session_signing_secret = "agent-identity-dev-secret"  # Only allowed in dev
        self.session_ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "43200"))
        self.schema_path = ROOT_DIR / "schemas" / "json" / "agent-id-record.schema.json"
        self.agent_auth_url = os.getenv("AGENT_AUTH_URL", "")
        self.agent_auth_api_key = os.getenv("AGENT_AUTH_API_KEY", "")
        self.agent_auth_timeout_seconds = float(os.getenv("AGENT_AUTH_TIMEOUT_SECONDS", "3.0"))
        self.caas_api_gateway_url = os.getenv("CAAS_API_GATEWAY_URL", "")
        self.caas_api_key = os.getenv("CAAS_API_KEY", "")
        self.caas_timeout_seconds = float(os.getenv("CAAS_TIMEOUT_SECONDS", "3.0"))
        self.authzen_fail_open = os.getenv("AUTHZEN_FAIL_OPEN", "true").lower() == "true"
        self.redis_url = os.getenv("REDIS_URL", "")


settings = Settings()
