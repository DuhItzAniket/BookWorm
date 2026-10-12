from typing import Literal
from pydantic import Field
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
    qa_model_revision: str = "d378e310c8000d824954c1e76c943a0581b49f0c"
    qa_device: str = "cpu"
    qa_threshold: float = 0.08
    top_k: int = 5
    brave_search_api_key: str = ""
    demo_access_token: str = ""
    ocr_provider: Literal["disabled", "glypharis"] = "disabled"
    glypharis_model_path: str = ""
    ocr_min_native_chars: int = Field(default=40, ge=0)
    ocr_max_pages: int = Field(default=5, ge=1, le=50)
    ocr_render_dpi: int = Field(default=150, ge=72, le=300)
    ocr_max_pixels: int = Field(default=8_000_000, ge=1_000, le=20_000_000)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
