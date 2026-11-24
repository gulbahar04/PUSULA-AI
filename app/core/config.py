from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    app_name: str = "PUSULA-AI Kurumsal IT Destek Agentic RAG Copilot"
    app_env: str = "development"

    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # Web Search
    tavily_api_key: str = ""

    # Embedding
    embedding_model: str = "embeddinggemma:latest"
    ollama_base_url: str = "http://localhost:11434"

    # ChromaDB
    chroma_persist_directory: str = str(BASE_DIR / "chroma_data")
    chroma_collection_name: str = "company_it_kb"

    # RAG
    top_k: int = 4
    max_retries: int = 1

   # Security
    admin_api_key: str = ""

    # Storage
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")
    upload_dir: str = str(BASE_DIR / "uploads")
    trash_dir: str = str(BASE_DIR / "trash")
    sample_kb_dir: str = str(BASE_DIR / "data" / "sample_kb")


    @model_validator(mode="after")
    def validate_security(self):
        if not self.admin_api_key.strip():
            raise ValueError(
            "ADMIN_API_KEY .env dosyasında tanımlanmalıdır."
        )

        if self.admin_api_key in {
        "change-me",
        "change-this-secret",
        "admin",
        "password"
    }:
            raise ValueError(
            "Güvensiz varsayılan yönetici anahtarı kullanılamaz."
        )

        return self

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()