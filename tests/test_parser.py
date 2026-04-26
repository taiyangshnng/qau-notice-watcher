from __future__ import annotations

import unittest

from parser import extract_date, parse_notice_list
from sites import SiteConfig


class ParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.site = SiteConfig(
            id="sample",
            name="示例频道",
            url="https://www.qau.edu.cn/channel/tongzhi",
            source="示例来源",
            category="school",
            audience=("student", "teacher"),
        )

    def test_parse_basic_notice_list(self) -> None:
        html = """
        <ul class="news-list">
          <li><span>2026-04-20</span><a href="/content/abc" title="关于举办校园文化活动的通知">查看</a></li>
          <li><a href="info/123.htm">2026/04/19 青创比赛报名通知</a></li>
          <li><a href="/channel/tongzhi">通知公告</a></li>
        </ul>
        """

        notices = parse_notice_list(html, self.site, default_year=2026)

        self.assertEqual(len(notices), 2)
        self.assertEqual(notices[0]["title"], "关于举办校园文化活动的通知")
        self.assertEqual(notices[0]["url"], "https://www.qau.edu.cn/content/abc")
        self.assertEqual(notices[0]["date"], "2026-04-20")
        self.assertEqual(notices[1]["title"], "青创比赛报名通知")
        self.assertEqual(notices[1]["date"], "2026-04-19")

    def test_extract_month_day_uses_default_year(self) -> None:
        self.assertEqual(extract_date("发布时间：04-18", default_year=2026), "2026-04-18")


if __name__ == "__main__":
    unittest.main()

