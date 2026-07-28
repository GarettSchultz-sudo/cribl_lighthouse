"""Smoke tests for the read-only API surface, no network."""
from fastapi.testclient import TestClient

from lighthouse.api.app import app


def test_health_ok():
    with TestClient(app) as cx:
        r = cx.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert "fedramp_notices" in j["sources"]


def test_feed_empty_when_fresh():
    with TestClient(app) as cx:
        r = cx.get("/feed")
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_feeds_legacy_shape():
    with TestClient(app) as cx:
        r = cx.get("/feeds")
    assert r.status_code == 200
    j = r.json()
    assert "notices" in j
    assert "changelog" in j
    assert j["notices"]["abbr"] == "NTC"
    assert j["changelog"]["abbr"] == "CHG"


def test_review_queue_empty_when_fresh():
    with TestClient(app) as cx:
        r = cx.get("/review/queue")
    assert r.status_code == 200
    assert r.json()["count"] == 0
