"""Configuration management"""

from typing import Optional

from pydantic import Extra
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database
    db_name: str = "techbrief_db"
    db_user: str = "postgres"
    db_password: str = "postgres123"
    database_url: Optional[str] = None

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "mistral"

    # Server
    debug: bool = False
    log_level: str = "INFO"

    # Scheduler
    scheduler_enabled: bool = True
    research_schedule_hour: int = 9
    research_schedule_minute: int = 0

    # News sources
    news_sources_enabled: list[str] = [
        "hacker_news",
        "medium",
        "dev_to",
    ]

    # Slack Configuration
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_channel: str = "#techbrief"

    model_config = {
        "extra": Extra.ignore,
        "env_file": ".env",
        "case_sensitive": False,
    }

    def __init__(self, **data):
        super().__init__(**data)
        if not self.database_url:
            self.database_url = f"postgresql://{self.db_user}:{self.db_password}@" f"postgres:5432/{self.db_name}"


settings = Settings()
