from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BookWorm"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    api_version: str = "v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
