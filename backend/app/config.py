"""Application configuration, loaded from the environment (§14: no secrets in
the repo; config via env). Var names are listed in ``.env.example``.

Phase 0: these are read but nothing real uses them yet (routers are stubs, the
storage adapter is a stub). They exist so the app boots and the contract is
complete.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres connection string, e.g. postgresql+psycopg://user:pass@host:5432/db
    database_url: str = "postgresql+psycopg://my_buddy:my_buddy@db:5432/my_buddy"

    # Anthropic SDK key — server-side only, never reaches the client (§7).
    anthropic_api_key: str = ""

    # Claude model for generation + research (§7). Swappable without code changes.
    anthropic_model: str = "claude-opus-4-8"

    # Storage adapter selection (§3 / D3). "local" volume now ▸ "r2" later.
    storage_backend: str = "local"
    storage_local_path: str = "/data/storage"

    # Public base URL of the app (used for building absolute links).
    app_base_url: str = "http://localhost:8000"

    # Auth mode (§2 / D2). "cloudflare_access" = edge auth, no app auth code.
    auth_mode: str = "cloudflare_access"

    # Session secret (only used if auth_mode is app-level). Never commit a value.
    session_secret: str = ""


settings = Settings()
