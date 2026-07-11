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

    # Gemini / GCP (Phase 4–7)
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    gemini_timeout_seconds: float = 30.0
    use_gcp: bool = False
    gcp_project_id: str | None = None
    gcp_location: str = "us-central1"
    google_application_credentials: str | None = None
    storage_bucket: str | None = None


settings = Settings()
