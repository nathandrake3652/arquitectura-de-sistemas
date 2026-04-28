from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI SQLAlchemy PostgreSQL App"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/fastapi_db"

    @property
    def sqlalchemy_database_url(self) -> str:
        # Railway and other providers usually expose postgresql:// URLs.
        # SQLAlchemy defaults that scheme to psycopg2, but this project uses psycopg v3.
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
