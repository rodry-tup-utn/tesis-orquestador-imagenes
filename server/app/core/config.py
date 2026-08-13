from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    postgres_user: str = "admin"
    postgres_password: str = "admin"
    postgres_db: str = "orquestador_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    secret_key: str = "secret-key-dev"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    url_webhook_n8n: str = ""
    
    # Orthanc settings
    orthanc_url: str = "http://localhost:8042"
    orthanc_user: str = "admin"
    orthanc_password: str = "admin"

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
