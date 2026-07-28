from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from . import config
from .models import Draft, Item, ReviewRecord, ReviewStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id              TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    payload         TEXT NOT NULL,
    first_seen      TEXT NOT NULL,
    last_seen       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS items_source ON items(source_id);

CREATE TABLE IF NOT EXISTS reviews (
    item_id         TEXT PRIMARY KEY,
    status          TEXT NOT NULL,
    payload         TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    FOREIGN KEY(item_id) REFERENCES items(id)
);
CREATE INDEX IF NOT EXISTS reviews_status ON reviews(status);

CREATE TABLE IF NOT EXISTS amendments (
    item_id         TEXT NOT NULL,
    seen_at         TEXT NOT NULL,
    prev_hash       TEXT NOT NULL,
    new_hash        TEXT NOT NULL,
    diff            TEXT NOT NULL,
    PRIMARY KEY (item_id, seen_at)
);
"""


class Store:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.settings.db_path
        with self.connect() as cx:
            cx.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        cx = sqlite3.connect(self.db_path)
        cx.row_factory = sqlite3.Row
        try:
            yield cx
            cx.commit()
        finally:
            cx.close()

    # ---------- items ----------
    def get_item(self, item_id: str) -> Optional[Item]:
        with self.connect() as cx:
            r = cx.execute("SELECT payload FROM items WHERE id = ?", (item_id,)).fetchone()
        return Item.model_validate_json(r["payload"]) if r else None

    def upsert_item(self, item: Item) -> tuple[bool, Optional[str]]:
        """Insert or update. Returns (is_new, prev_hash_if_amended)."""
        existing = self.get_item(item.id)
        is_new = existing is None
        prev_hash = None
        if existing and existing.content_hash != item.content_hash:
            prev_hash = existing.content_hash
            item.first_seen = existing.first_seen
        elif existing:
            item.first_seen = existing.first_seen

        with self.connect() as cx:
            cx.execute(
                """INSERT INTO items(id, source_id, content_hash, payload, first_seen, last_seen)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     source_id=excluded.source_id,
                     content_hash=excluded.content_hash,
                     payload=excluded.payload,
                     last_seen=excluded.last_seen""",
                (
                    item.id,
                    item.source_id,
                    item.content_hash,
                    item.model_dump_json(),
                    item.first_seen.isoformat(),
                    item.last_seen.isoformat(),
                ),
            )
        return is_new, prev_hash

    def record_amendment(self, item_id: str, prev_hash: str, new_hash: str, diff: dict) -> None:
        with self.connect() as cx:
            cx.execute(
                "INSERT OR REPLACE INTO amendments(item_id, seen_at, prev_hash, new_hash, diff) VALUES (?,?,?,?,?)",
                (item_id, datetime.utcnow().isoformat(), prev_hash, new_hash, json.dumps(diff)),
            )

    def list_items(self) -> list[Item]:
        with self.connect() as cx:
            rows = cx.execute("SELECT payload FROM items ORDER BY last_seen DESC").fetchall()
        return [Item.model_validate_json(r["payload"]) for r in rows]

    def list_items_by_source(self, source_id: str) -> list[Item]:
        with self.connect() as cx:
            rows = cx.execute(
                "SELECT payload FROM items WHERE source_id = ? ORDER BY last_seen DESC",
                (source_id,),
            ).fetchall()
        return [Item.model_validate_json(r["payload"]) for r in rows]

    # ---------- reviews ----------
    def upsert_review(self, rec: ReviewRecord) -> None:
        with self.connect() as cx:
            cx.execute(
                """INSERT INTO reviews(item_id, status, payload, updated_at)
                   VALUES (?,?,?,?)
                   ON CONFLICT(item_id) DO UPDATE SET
                     status=excluded.status,
                     payload=excluded.payload,
                     updated_at=excluded.updated_at""",
                (rec.item_id, rec.status.value, rec.model_dump_json(), rec.updated_at.isoformat()),
            )

    def get_review(self, item_id: str) -> Optional[ReviewRecord]:
        with self.connect() as cx:
            r = cx.execute("SELECT payload FROM reviews WHERE item_id = ?", (item_id,)).fetchone()
        return ReviewRecord.model_validate_json(r["payload"]) if r else None

    def list_reviews(self, status: Optional[ReviewStatus] = None) -> list[ReviewRecord]:
        with self.connect() as cx:
            if status:
                rows = cx.execute(
                    "SELECT payload FROM reviews WHERE status = ? ORDER BY updated_at DESC",
                    (status.value,),
                ).fetchall()
            else:
                rows = cx.execute("SELECT payload FROM reviews ORDER BY updated_at DESC").fetchall()
        return [ReviewRecord.model_validate_json(r["payload"]) for r in rows]

    def has_draft(self, item_id: str) -> bool:
        with self.connect() as cx:
            r = cx.execute("SELECT 1 FROM reviews WHERE item_id = ?", (item_id,)).fetchone()
        return r is not None
