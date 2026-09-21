from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    postgres_user: str = "admin"
    postgres_password: str = "admin"
    postgres_db: str = "orquestador_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    secret_key: str
    pseudonym_secret: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    auth_username: str = "admin"
    auth_password: str = ""
    internal_api_key: str = ""
    alert_webhook_key: str = ""
    url_webhook_n8n: str = ""
    triage_config: str = "desplegada"
    
    # Orthanc settings
    orthanc_url: str = "http://localhost:8042"
    orthanc_user: str = ""
    orthanc_password: str = ""

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
