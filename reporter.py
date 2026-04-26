"""Markdown and JSON report writers."""

from __future__ import annotations

import json
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


GROUP_NAMES = (
    "学生活动",
    "本科生教务",
    "研究生事务",
    "教师教学通知",
    "人事与招聘",
    "信息化通知",
    "学校级公告",
    "其他",
)


def write_daily_report(
    notices: list[dict],
    path: str | Path = "daily.md",
    *,
    init_mode: bool = False,
    preview_mode: bool = False,
    initialized_count: int = 0,
) -> None:
    now = _now_beijing()
    grouped = _group_notices(notices)
    activity_count = sum(
        1
        for notice in notices
        if set(notice.get("tags", [])) & {"activity", "competition", "volunteer"}
    )

    lines = [
        "# 青岛农业大学每日通知摘要",
        "",
        f"生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')} 北京时间",
        f"今日新增通知总数：{0 if init_mode else len(notices)}",
        f"活动类通知数量：{0 if init_mode else activity_count}",
        "",
    ]

    if init_mode:
        lines.extend(
            [
                "初始化模式：已将当前抓到的通知写入去重库，本次不输出新增通知。",
                f"本次新增基线记录：{initialized_count}",
                "",
            ]
        )
    elif preview_mode:
        lines.extend(["预览模式：以下为当前列表页可解析通知，不会写入去重库。", ""])
        if notices:
            _append_grouped_notices(lines, grouped)
        else:
            lines.extend(["当前列表暂无可显示通知", ""])
    elif not notices:
        lines.extend(["今日暂无新增通知", ""])
    else:
        _append_grouped_notices(lines, grouped)

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_crawl_log(log: dict, path: str | Path = "crawl_log.json") -> None:
    Path(path).write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _append_grouped_notices(lines: list[str], grouped: OrderedDict[str, list[dict]]) -> None:
    for group_name in GROUP_NAMES:
        group_items = grouped[group_name]
        if not group_items:
            continue
        lines.extend([f"## {group_name}", ""])
        for notice in group_items:
            tags = ", ".join(notice.get("tags", [])) or "other"
            date = notice.get("date") or "日期未知"
            audience = ", ".join(notice.get("audience", []))
            lines.extend(
                [
                    f"- 【{notice.get('source', '未知来源')}】[{notice.get('title', '')}]({notice.get('url', '')})",
                    f"  - 日期：{date}",
                    f"  - 标签：{tags}",
                    f"  - 对象：{audience or '未标注'}",
                ]
            )
        lines.append("")


def _group_notices(notices: list[dict]) -> OrderedDict[str, list[dict]]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict((name, []) for name in GROUP_NAMES)
    for notice in notices:
        grouped[_group_name(notice)].append(notice)
    return grouped


def _group_name(notice: dict) -> str:
    category = notice.get("category", "")
    tags = set(notice.get("tags", []))

    if tags & {"activity", "competition", "volunteer"} or category == "youth":
        return "学生活动"
    if category == "undergraduate_teaching" or tags & {"exam", "scholarship"}:
        return "本科生教务"
    if category == "graduate":
        return "研究生事务"
    if category == "teacher_teaching":
        return "教师教学通知"
    if category == "hr" or tags & {"employment", "hr"}:
        return "人事与招聘"
    if category == "it" or "it_notice" in tags:
        return "信息化通知"
    if category == "school" or "admin" in tags:
        return "学校级公告"
    return "其他"


def _now_beijing() -> datetime:
    try:
        return datetime.now(ZoneInfo("Asia/Shanghai"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=8)))
