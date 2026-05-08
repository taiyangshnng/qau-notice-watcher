"""QAU daily public notice watcher."""

from __future__ import annotations

import argparse
import random
import time
from datetime import datetime
from typing import Any

import requests

from classifier import classify_notice
from mailer import send_daily_email
from parser import parse_notice_list
from reporter import daily_report_archive_path, write_crawl_log, write_daily_report
from sites import SITES, SiteConfig
from storage import NoticeStorage


USER_AGENT = (
    "qau-notice-watcher/0.1 "
    "(personal campus notice aggregation; low-frequency; contact: GitHub Actions)"
)
TIMEOUT_SECONDS = 10
MAX_RETRIES = 1
SKIP_RETRY_STATUSES = {403, 429}


def main() -> int:
    args = _parse_args()
    started_at = datetime.now().isoformat(timespec="seconds")
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    storage = NoticeStorage(args.db)
    new_notices: list[dict[str, Any]] = []
    initialized_count = 0
    channel_logs: list[dict[str, Any]] = []
    mail_log: dict[str, Any] = {
        "enabled": False,
        "sent": False,
        "error": None,
    }

    try:
        for index, site in enumerate(SITES):
            channel_log, notices = crawl_site(session, site)
            channel_logs.append(channel_log)

            if notices:
                for notice in notices:
                    notice["tags"] = classify_notice(
                        notice.get("title", ""),
                        notice.get("source", ""),
                        notice.get("category", ""),
                    )
                    if args.preview:
                        new_notices.append(notice)
                        channel_log["new_count"] += 1
                        continue

                    was_new = storage.add_if_new(notice)
                    if was_new:
                        if args.init:
                            initialized_count += 1
                        else:
                            new_notices.append(notice)
                            channel_log["new_count"] += 1

            if index < len(SITES) - 1 and not args.skip_sleep:
                time.sleep(random.uniform(3, 8))
    finally:
        storage.close()

    finished_at = datetime.now().isoformat(timespec="seconds")
    log = {
        "started_at": started_at,
        "finished_at": finished_at,
        "init_mode": args.init,
        "preview_mode": args.preview,
        "total_channels": len(SITES),
        "successful_channels": sum(1 for item in channel_logs if item["status"] == "ok"),
        "total_new": 0 if args.init else len(new_notices),
        "initialized_count": initialized_count,
        "channels": channel_logs,
    }

    archive_path = None
    if not args.preview and not args.no_archive:
        archive_path = daily_report_archive_path(args.archive_dir)

    written_archive = write_daily_report(
        new_notices,
        args.daily,
        archive_path=archive_path,
        init_mode=args.init,
        preview_mode=args.preview,
        initialized_count=initialized_count,
    )

    if new_notices and not args.init and not args.preview and not args.no_mail:
        mail_log = send_daily_email(args.daily)

    log["mail"] = mail_log
    log["reports"] = {
        "latest": args.daily,
        "archive": str(written_archive) if written_archive else None,
    }
    write_crawl_log(log, args.log)

    mode = "preview" if args.preview else "init" if args.init else "normal"
    print(
        f"Done. mode={mode} channels={len(channel_logs)} "
        f"displayed={len(new_notices)} initialized={initialized_count}"
    )
    return 0


def crawl_site(session: requests.Session, site: SiteConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    channel_log: dict[str, Any] = {
        "id": site.id,
        "name": site.name,
        "url": site.url,
        "status": "pending",
        "http_status": None,
        "attempts": 0,
        "parsed_count": 0,
        "new_count": 0,
        "error": None,
    }

    response, error, attempts = fetch_page(session, site.url)
    channel_log["attempts"] = attempts
    if error:
        channel_log["status"] = "failed"
        channel_log["error"] = error
        return channel_log, []

    assert response is not None
    channel_log["http_status"] = response.status_code
    if not response.ok:
        channel_log["status"] = "http_error"
        channel_log["error"] = f"HTTP {response.status_code}"
        return channel_log, []

    response.encoding = response.apparent_encoding or response.encoding
    try:
        notices = parse_notice_list(response.text, site)
    except Exception as exc:  # Keep one bad page from stopping the full run.
        channel_log["status"] = "parse_error"
        channel_log["error"] = f"{type(exc).__name__}: {exc}"
        return channel_log, []

    channel_log["status"] = "ok"
    channel_log["parsed_count"] = len(notices)
    return channel_log, notices


def fetch_page(
    session: requests.Session,
    url: str,
    *,
    timeout: int = TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES,
) -> tuple[requests.Response | None, str | None, int]:
    attempts = 0
    last_error: str | None = None

    while attempts <= max_retries:
        attempts += 1
        try:
            response = session.get(url, timeout=timeout)
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempts > max_retries:
                return None, last_error, attempts
            time.sleep(1)
            continue

        if response.status_code in SKIP_RETRY_STATUSES or response.status_code >= 500:
            return response, None, attempts
        return response, None, attempts

    return None, last_error or "Unknown fetch error", attempts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QAU daily public notice watcher")
    parser.add_argument("--init", action="store_true", help="建立去重基线，不输出新增通知")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="预览当前列表页可解析通知，不写入去重库",
    )
    parser.add_argument("--db", default="data/seen.sqlite", help="SQLite 去重库路径")
    parser.add_argument("--daily", default="daily.md", help="Markdown 摘要输出路径")
    parser.add_argument("--archive-dir", default="reports", help="每日历史摘要保存目录")
    parser.add_argument("--log", default="crawl_log.json", help="抓取日志输出路径")
    parser.add_argument("--no-mail", action="store_true", help="即使有新增通知也不发送邮件")
    parser.add_argument("--no-archive", action="store_true", help="不保存每日历史摘要")
    parser.add_argument(
        "--skip-sleep",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    if args.init and args.preview:
        parser.error("--init 和 --preview 不能同时使用")
    return args


if __name__ == "__main__":
    raise SystemExit(main())
