from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Arabic Editorial Proofreading Engine"
    ai_client: str = "mock"  # mock | gemini
    rules_dir: Path = ROOT_DIR / "data" / "rules"
    entities_dir: Path = ROOT_DIR / "data" / "entities"
    spelling_replacements_path: Path = ROOT_DIR / "data" / "spelling" / "replacements.json"
    editorial_phrases_path: Path = (
        ROOT_DIR / "data" / "lexicons" / "editorial_phrases.json"
    )
    grammar_patterns_path: Path = (
        ROOT_DIR / "data" / "lexicons" / "grammar_patterns.json"
    )
    golden_editorial_path: Path = (
        ROOT_DIR / "data" / "evaluation" / "golden_editorial.jsonl"
    )
    sqlite_path: Path = ROOT_DIR / "data" / "app.db"
    fuzzy_taa_marbuta: bool = False
    # Alef-variant soft warnings are noisy for POC demos; off by default.
    enable_letter_variant_warnings: bool = False
    # Punctuation policy: off | strict | full (default strict — suppress style noise)
    punctuation_policy: str = "strict"

    # Demo auth — read from .env on every startup (change ADMIN_PASSWORD there)
    public_password: str = "demo"
    admin_password: str = "302@Labs"
    # When false, API is open (local tests). Set DEMO_AUTH_REQUIRED=true for gated demo.
    demo_auth_required: bool = True

    # Gemini / GCP (Phase 4–7)
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    gemini_timeout_seconds: float = 30.0
    use_gcp: bool = False
    gcp_project_id: str | None = None
    gcp_location: str = "us-central1"
    google_application_credentials: str | None = None
    storage_bucket: str | None = None

    # Cloud Run / demo hosting — comma-separated origins (* allowed for open demo)
    cors_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:3000,http://localhost:3000"
    )

    # Dataset storage (local vs GCS) — local works without GCP credentials
    data_backend: str = "local"  # local | gcs
    local_data_dir: Path = ROOT_DIR / "data" / "local"
    gcs_data_bucket: str = "arabic-proofreading-data-ooredoo-499510"
    gcs_data_prefix: str = ""
    data_cache_dir: Path = ROOT_DIR / "data" / "cache"
    data_cache_enabled: bool = True


settings = Settings()
