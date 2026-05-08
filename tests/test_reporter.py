from __future__ import annotations

import unittest
from pathlib import Path
from uuid import uuid4

from reporter import write_daily_report


class ReporterTests(unittest.TestCase):
    def test_write_daily_report_also_writes_archive(self) -> None:
        root = Path(".test-tmp") / f"reporter-archive-{uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        latest = root / "daily.md"
        archive = root / "reports" / "2026-05-08.md"

        written = write_daily_report(
            [],
            latest,
            archive_path=archive,
        )

        self.assertEqual(written, archive)
        self.assertTrue(latest.exists())
        self.assertTrue(archive.exists())
        self.assertEqual(
            latest.read_text(encoding="utf-8"),
            archive.read_text(encoding="utf-8"),
        )

    def test_empty_later_run_does_not_overwrite_existing_archive(self) -> None:
        root = Path(".test-tmp") / f"reporter-preserve-{uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        latest = root / "daily.md"
        archive = root / "reports" / "2026-05-08.md"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text("早上已经保存的通知", encoding="utf-8")

        written = write_daily_report([], latest, archive_path=archive)

        self.assertEqual(written, archive)
        self.assertEqual(archive.read_text(encoding="utf-8"), "早上已经保存的通知")
        self.assertIn("今日暂无新增通知", latest.read_text(encoding="utf-8"))

    def test_later_run_with_new_notices_appends_to_existing_archive(self) -> None:
        root = Path(".test-tmp") / f"reporter-append-{uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        latest = root / "daily.md"
        archive = root / "reports" / "2026-05-08.md"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text("早上已经保存的通知", encoding="utf-8")

        write_daily_report(
            [
                {
                    "title": "下午新增通知",
                    "url": "https://www.qau.edu.cn/content/tongzhi/demo",
                    "date": "2026-05-08",
                    "source": "学校官网",
                    "category": "school",
                    "audience": ["student"],
                    "tags": ["admin"],
                }
            ],
            latest,
            archive_path=archive,
        )

        content = archive.read_text(encoding="utf-8")
        self.assertIn("早上已经保存的通知", content)
        self.assertIn("下午新增通知", content)
        self.assertIn("---", content)


if __name__ == "__main__":
    unittest.main()
