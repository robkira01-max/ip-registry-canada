"""Configuration centralisée via variables d'environnement."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        extra="ignore",
    )

    # App
    app_name: str = "RegistreIP-Canada"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql://ipregistry:changeme@localhost:5432/ip_registry"

    # JWT RS256
    jwt_private_key_path: str = "/app/keys/private.pem"
    jwt_public_key_path: str = "/app/keys/public.pem"
    jwt_algorithm: str = "RS256"
    access_token_expire_minutes: int = 60

    # OPIC / CIPO external APIs
    cipo_base_url: str = "https://www.ic.gc.ca/opic-cipo/cpd/eng"
    pct_base_url: str = "https://www.wipo.int/pctdb/en"

    # Storage
    upload_dir: str = "/data/uploads"
    export_dir: str = "/data/exports"

    @property
    def jwt_private_key(self) -> str:
        path = Path(self.jwt_private_key_path)
        return path.read_text() if path.exists() else ""

    @property
    def jwt_public_key(self) -> str:
        path = Path(self.jwt_public_key_path)
        return path.read_text() if path.exists() else ""


settings = Settings()
