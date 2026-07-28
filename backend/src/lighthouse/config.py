from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-opus-4-7"

    slack_bot_token: Optional[str] = None
    slack_review_channel: str = "#lighthouse-review"
    slack_signing_secret: Optional[str] = None

    jira_base_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_project_key: Optional[str] = None
    jira_epic_issue_type: str = "Epic"
    jira_story_issue_type: str = "Story"

    lighthouse_sources: str = ""
    lighthouse_poll_interval_minutes: int = 180
    lighthouse_db_path: str = "./data/lighthouse.db"
    lighthouse_today_override: Optional[str] = None

    @property
    def db_path(self) -> Path:
        p = Path(self.lighthouse_db_path)
        if not p.is_absolute():
            p = BACKEND_ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def outbox_root(self) -> Path:
        p = BACKEND_ROOT / "outbox"
        (p / "slack").mkdir(parents=True, exist_ok=True)
        (p / "jira").mkdir(parents=True, exist_ok=True)
        return p

    @property
    def enabled_source_ids(self) -> Optional[set[str]]:
        if not self.lighthouse_sources.strip():
            return None
        return {s.strip() for s in self.lighthouse_sources.split(",") if s.strip()}

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def slack_enabled(self) -> bool:
        return bool(self.slack_bot_token)

    @property
    def jira_enabled(self) -> bool:
        return bool(self.jira_base_url and self.jira_email and self.jira_api_token and self.jira_project_key)


settings = Settings()
