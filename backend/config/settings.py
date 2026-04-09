"""
settings.py
-----------
Centralised configuration using Pydantic Settings.
Values are read from environment variables or the .env file automatically.

HOW TO USE:
    from config.settings import settings
    print(settings.postgres_host)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configurable values for the application.
    Pydantic reads these from environment variables (case-insensitive)
    or from a .env file in the project root.
    """

    # ----- Postgres -----
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db:   str = "rag_db"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # ----- Ollama -----
    ollama_base_url:   str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    # ----- RAG -----
    chunk_size:    int = 512
    chunk_overlap: int = 64
    top_k_results: int = 5

    # ----- API -----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:5500"

    # TODO: add any extra settings you need here

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def postgres_dsn(self) -> str:
        """Build the full Postgres connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a Python list."""
        return [o.strip() for o in self.cors_origins.split(",")]


# Singleton — import this everywhere
settings = Settings()
