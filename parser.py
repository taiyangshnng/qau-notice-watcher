"""HTML list parser for public notice pages."""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup


FULL_DATE_PATTERNS = (
    re.compile(r"(20\d{2})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})\s*日?"),
)
MONTH_DAY_PATTERNS = (
    re.compile(r"(?<!\d)(\d{1,2})\s*[-/.月]\s*(\d{1,2})\s*日?(?!\d)"),
)

NOISE_TITLES = {
    "首页",
    "通知公告",
    "团学信息",
    "学生通知",
    "教师通知",
    "更多",
    "更多>>",
    "more",
    "下一页",
    "上一页",
}

DOWNLOAD_SUFFIXES = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".css",
    ".js",
    ".ico",
    ".zip",
    ".rar",
)


def parse_notice_list(
    html: str,
    site: Any,
    *,
    default_year: int | None = None,
) -> list[dict[str, Any]]:
    """Parse notice links from a channel list page."""

    soup = BeautifulSoup(html, "html.parser")
    base_url = _site_value(site, "url")
    default_year = default_year or date.today().year
    notices: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if _should_skip_href(href):
            continue

        raw_title = _raw_anchor_title(anchor)
        title = _extract_title(anchor)
        if _is_noise_title(title):
            continue

        absolute_url = _make_absolute_url(base_url, href)
        if not absolute_url or absolute_url in seen_urls:
            continue
        if not _same_site(base_url, absolute_url):
            continue

        context = _find_context_text(anchor)
        notice_date = extract_date(f"{context} {raw_title}", default_year=default_year)
        looks_like_detail = _looks_like_detail_href(href)
        if not notice_date and not looks_like_detail:
            continue

        score = _score_candidate(anchor, href, title, context, notice_date)
        if score < 3:
            continue

        seen_urls.add(absolute_url)
        notices.append(
            {
                "title": title,
                "url": absolute_url,
                "date": notice_date or "",
                "source": _site_value(site, "source"),
                "category": _site_value(site, "category"),
                "audience": list(_site_value(site, "audience", ())),
                "tags": [],
            }
        )

    return notices


def extract_date(text: str, *, default_year: int | None = None) -> str:
    """Extract YYYY-MM-DD from nearby list text."""

    default_year = default_year or date.today().year
    normalized = _clean_text(text)

    for pattern in FULL_DATE_PATTERNS:
        match = pattern.search(normalized)
        if match:
            year, month, day = (int(part) for part in match.groups())
            return _format_date(year, month, day)

    for pattern in MONTH_DAY_PATTERNS:
        match = pattern.search(normalized)
        if match:
            month, day = (int(part) for part in match.groups())
            return _format_date(default_year, month, day)

    return ""


def _site_value(site: Any, key: str, default: Any = "") -> Any:
    if isinstance(site, dict):
        return site.get(key, default)
    return getattr(site, key, default)


def _extract_title(anchor: Any) -> str:
    return _strip_date_prefix(_raw_anchor_title(anchor))


def _raw_anchor_title(anchor: Any) -> str:
    title_attr = _clean_text(anchor.get("title", ""))
    text = _clean_text(anchor.get_text(" ", strip=True))
    return title_attr if len(title_attr) >= len(text) else text


def _strip_date_prefix(title: str) -> str:
    title = re.sub(r"^[\[【(（]?\s*20\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}\s*日?\s*[\]】)）]?\s*", "", title)
    title = re.sub(r"^[\[【(（]?\s*\d{1,2}\s*[-/.月]\s*\d{1,2}\s*日?\s*[\]】)）]?\s*", "", title)
    return _clean_text(title)


def _find_context_text(anchor: Any) -> str:
    node = anchor
    collected: list[str] = []
    for _ in range(5):
        node = node.parent
        if node is None:
            break
        text = _clean_text(node.get_text(" ", strip=True))
        if text:
            collected.append(text)
        if node.name in {"li", "tr"} and text:
            return text
        anchor_count = len(node.find_all("a", href=True))
        if len(text) <= 400 and anchor_count <= 1 and extract_date(text):
            return text
    return collected[0] if collected else ""


def _score_candidate(anchor: Any, href: str, title: str, context: str, notice_date: str) -> int:
    score = 0
    if notice_date:
        score += 3
    if _looks_like_detail_href(href):
        score += 3
    if anchor.find_parent(["li", "tr"]):
        score += 2
    if len(title) >= 8:
        score += 1
    if 0 < len(context) <= 300:
        score += 1
    return score


def _looks_like_detail_href(href: str) -> bool:
    lowered = href.lower()
    if "/channel/" in lowered:
        return False
    return any(
        part in lowered
        for part in (
            "/content/",
            "/info/",
            "article",
            "detail",
            "newscontent",
            ".htm",
            ".html",
        )
    )


def _make_absolute_url(base_url: str, href: str) -> str:
    absolute = urljoin(base_url, href)
    absolute, _fragment = urldefrag(absolute)
    parsed = urlsplit(absolute)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return absolute


def _same_site(base_url: str, absolute_url: str) -> bool:
    return urlsplit(base_url).netloc.lower() == urlsplit(absolute_url).netloc.lower()


def _should_skip_href(href: str) -> bool:
    lowered = href.lower().strip()
    if not lowered or lowered.startswith(("#", "javascript:", "mailto:", "tel:")):
        return True
    return lowered.endswith(DOWNLOAD_SUFFIXES)


def _is_noise_title(title: str) -> bool:
    lowered = title.lower()
    return len(title) < 4 or title in NOISE_TITLES or lowered in NOISE_TITLES


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip(" \t\r\n·•|-")


def _format_date(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""
