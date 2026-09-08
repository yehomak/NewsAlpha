from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/butterfly_effect"
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    log_level: str = "INFO"
    app_env: str = "development"
    # ingestion
    alpaca_key: str = ""
    alpaca_secret: str = ""
    ingest_interval_hours: int = 1
    ingest_max_age_days: int = 7
    # pipeline
    anthropic_api_key: str = ""
    pipeline_interval_minutes: int = 30
    pipeline_batch_size: int = 25
    pipeline_max_age_days: int = 2  # only run LLM on articles ≤2 days old; ingest still keeps 7
    # eval
    eval_interval_hours: int = 6
    # dashboard
    cors_origins: list[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
