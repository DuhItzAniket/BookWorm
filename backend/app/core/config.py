from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BookWorm"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    api_version: str = "v1"
    database_url: str = "sqlite:///./bookworm.db"
    upload_dir: str = "./storage/uploads"
    temp_dir: str = "./storage/tmp"
    max_file_size_mb: int = 20
    max_pages: int = 500
    max_extracted_chars: int = 2_000_000
    qa_model_name: str = "deepset/bert-base-cased-squad2"
    qa_device: str = "cpu"
    qa_threshold: float = 0.08
    top_k: int = 5
    brave_search_api_key: str = ""
    demo_access_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
