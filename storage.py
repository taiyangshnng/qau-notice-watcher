"""SQLite persistence for seen notices."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
}


class NoticeStorage:
    def __init__(self, db_path: str | Path = "data/seen.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def add_if_new(self, notice: dict) -> bool:
        notice["url"] = normalize_url(notice["url"])
        now = datetime.now().isoformat(timespec="seconds")
        cursor = self.conn.execute(
            """
            INSERT OR IGNORE INTO seen_notices
                (url, title, date, source, category, audience, tags, first_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notice["url"],
                notice.get("title", ""),
                notice.get("date", ""),
                notice.get("source", ""),
                notice.get("category", ""),
                json.dumps(notice.get("audience", []), ensure_ascii=False),
                json.dumps(notice.get("tags", []), ensure_ascii=False),
                now,
            ),
        )
        self.conn.commit()
        return cursor.rowcount == 1

    def seen_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS count FROM seen_notices").fetchone()
        return int(row["count"])

    def close(self) -> None:
        self.conn.close()

    def _setup(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_notices (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT,
                source TEXT,
                category TEXT,
                audience TEXT,
                tags TEXT,
                first_seen_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()


def normalize_url(raw_url: str) -> str:
    """Normalize URLs enough to keep the same notice from appearing twice."""

    parsed = urlsplit((raw_url or "").strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    if netloc.endswith("qau.edu.cn"):
        scheme = "https"

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_KEYS
    ]
    query = urlencode(sorted(query_items), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))

