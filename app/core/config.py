from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "trade-challenges-agent"
    environment: str = "dev"

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    # Search providers
    search_provider: Literal["bing", "serpapi"] = Field(default="serpapi", alias="SEARCH_PROVIDER")
    azure_bing_key: Optional[str] = Field(default=None, alias="AZURE_BING_KEY")
    azure_bing_endpoint: str = Field(default="https://api.bing.microsoft.com/v7.0/search", alias="AZURE_BING_ENDPOINT")
    serpapi_key: Optional[str] = Field(default=None, alias="SERPAPI_KEY")

    # Fetching
    request_timeout_s: int = Field(default=15, alias="REQUEST_TIMEOUT_S")
    rate_limit_per_domain_s: float = Field(default=1.0, alias="RATE_LIMIT_PER_DOMAIN_S")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    user_agent: str = Field(default="TradeChallengesBot/1.0 (+contact: research@example.com)", alias="USER_AGENT")

    # Pipeline
    top_n_per_query: int = Field(default=5, alias="TOP_N_PER_QUERY")
    max_items: int = Field(default=20, alias="MAX_ITEMS")
    recency_days: int = Field(default=60, alias="RECENCY_DAYS")
    dry_run: bool = Field(default=False, alias="DRY_RUN")

    # Storage
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    database_url: str = Field(default="postgresql+psycopg2://trade:trade@localhost:5432/trade_challenges", alias="DATABASE_URL")


settings = Settings()
