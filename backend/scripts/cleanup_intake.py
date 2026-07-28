"""One-shot cleanup of the local DB to reflect demo policy:

  1. Remove Federal Register entries that aren't actually FedRAMP-relevant
     (Privacy Act SORNs etc. that mention FedRAMP only in passing).
  2. Tag the 6 informational FedRAMP notices and 12 FRMR/Changelog items
     as needs_action=false so they appear as reference-only in the feed.
  3. Delete their auto-generated mock drafts so the review queue stays
     focused on real action items.

Idempotent — run as many times as you like.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lighthouse.config import settings
from lighthouse.sources.federal_register import _is_fedramp_relevant
from lighthouse.store import Store


INFORMATIONAL_NOTICES = {"NTC-0001", "NTC-0002", "NTC-0003", "NTC-0005", "NTC-0007", "NTC-0011"}


def main() -> None:
    s = Store()
    items = s.list_items()

    removed_fr = 0
    tagged_info = 0
    tagged_ref = 0

    for it in items:
        # 1. Federal Register relevance filter.
        if it.source_id == "federal_register":
            if not _is_fedramp_relevant(it.title, it.summary):
                # Hard-delete the item + its draft.
                with s.connect() as cx:
                    cx.execute("DELETE FROM items WHERE id = ?", (it.id,))
                    cx.execute("DELETE FROM reviews WHERE item_id = ?", (it.id,))
                removed_fr += 1
                continue

        # 2. Informational FedRAMP notices — flag as reference-only.
        if it.id in INFORMATIONAL_NOTICES:
            it.needs_action = False
            it.content_hash = it.content_hash + "_info"
            s.upsert_item(it)
            with s.connect() as cx:
                cx.execute("DELETE FROM reviews WHERE item_id = ?", (it.id,))
            tagged_info += 1
            continue

        # 3. FRMR + Changelog — reference-only by nature.
        if it.source_id in ("frmr", "fedramp_changelog"):
            it.needs_action = False
            it.content_hash = it.content_hash + "_ref"
            s.upsert_item(it)
            with s.connect() as cx:
                cx.execute("DELETE FROM reviews WHERE item_id = ?", (it.id,))
            tagged_ref += 1

    print(f"removed Federal Register noise: {removed_fr}")
    print(f"tagged informational notices:   {tagged_info}")
    print(f"tagged reference items:         {tagged_ref}")
    print(f"items remaining: {len(s.list_items())}")


if __name__ == "__main__":
    main()
