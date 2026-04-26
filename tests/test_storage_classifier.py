from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from classifier import classify_notice
from storage import NoticeStorage, normalize_url


class StorageAndClassifierTests(unittest.TestCase):
    def test_storage_deduplicates_normalized_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "seen.sqlite"
            storage = NoticeStorage(db_path)
            try:
                notice = {
                    "title": "测试通知",
                    "url": "http://www.qau.edu.cn/content/tongzhi/demo/?utm_source=x",
                    "date": "2026-04-26",
                    "source": "学校官网",
                    "category": "school",
                    "audience": ["student"],
                    "tags": ["admin"],
                }

                self.assertTrue(storage.add_if_new(dict(notice)))
                self.assertFalse(storage.add_if_new(dict(notice)))
                self.assertEqual(storage.seen_count(), 1)
            finally:
                storage.close()

    def test_normalize_url_handles_tracking_and_scheme(self) -> None:
        self.assertEqual(
            normalize_url("http://www.qau.edu.cn/content/tongzhi/demo/?utm_source=x"),
            "https://www.qau.edu.cn/content/tongzhi/demo",
        )

    def test_classifier_marks_activity_notice(self) -> None:
        tags = classify_notice("关于举办大学生社团文化节活动的通知", "校团委", "youth")
        self.assertIn("activity", tags)
        self.assertIn("admin", tags)


if __name__ == "__main__":
    unittest.main()

