"""Keyword-based notice classifier."""

from __future__ import annotations


CATEGORY_DEFAULT_TAGS = {
    "hr": "hr",
    "it": "it_notice",
}


KEYWORD_TAGS: dict[str, tuple[str, ...]] = {
    "competition": (
        "竞赛",
        "比赛",
        "大赛",
        "挑战赛",
        "创新创业",
        "创业",
        "征集",
        "评选",
    ),
    "volunteer": (
        "志愿",
        "志愿者",
        "公益",
        "支教",
        "服务队",
        "社会实践",
    ),
    "activity": (
        "活动",
        "报名",
        "培训",
        "社团",
        "团日",
        "文体",
        "实践",
        "招募",
    ),
    "academic": (
        "学术",
        "讲座",
        "论坛",
        "报告会",
        "研讨",
        "科研",
        "论文",
        "课题",
    ),
    "exam": (
        "考试",
        "补考",
        "缓考",
        "四六级",
        "等级考试",
        "成绩",
        "选课",
        "重修",
    ),
    "scholarship": (
        "奖学金",
        "助学金",
        "资助",
        "困难认定",
        "助学贷款",
        "勤工助学",
    ),
    "employment": (
        "就业",
        "招聘",
        "双选会",
        "宣讲会",
        "岗位",
        "实习",
        "求职",
        "人才引进",
    ),
    "hr": (
        "人事",
        "职称",
        "聘用",
        "聘任",
        "考核",
        "师资",
        "人才",
    ),
    "it_notice": (
        "网络",
        "信息化",
        "系统",
        "vpn",
        "邮箱",
        "统一身份认证",
        "服务器",
        "数据",
        "智慧校园",
        "域名",
    ),
    "admin": (
        "通知",
        "公告",
        "安排",
        "公示",
        "值班",
        "放假",
        "调休",
        "会议",
    ),
}


def classify_notice(title: str, source: str = "", category: str = "") -> list[str]:
    """Return stable tags for a notice title."""

    text = f"{title} {source} {category}".lower()
    tags: list[str] = []

    default_tag = CATEGORY_DEFAULT_TAGS.get(category)
    if default_tag:
        tags.append(default_tag)

    for tag, keywords in KEYWORD_TAGS.items():
        if any(keyword.lower() in text for keyword in keywords):
            tags.append(tag)

    deduped = list(dict.fromkeys(tags))
    return deduped or ["other"]

