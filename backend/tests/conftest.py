import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    """Each test gets its own DB + outbox dir, no creds."""
    db = tmp_path / "lighthouse.db"
    monkeypatch.setenv("LIGHTHOUSE_DB_PATH", str(db))
    monkeypatch.setenv("LIGHTHOUSE_DISABLE_SCHEDULER", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)

    # Force settings re-read for the new env.
    from lighthouse import config

    config.settings = config.Settings()
    yield
