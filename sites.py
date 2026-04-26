"""Configured public QAU notice channels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SiteConfig:
    id: str
    name: str
    url: str
    source: str
    category: str
    audience: tuple[str, ...]


SITES: tuple[SiteConfig, ...] = (
    SiteConfig(
        id="qau_main_notices",
        name="学校官网-通知公告",
        url="https://www.qau.edu.cn/channel/tongzhi",
        source="学校官网",
        category="school",
        audience=("student", "teacher", "staff"),
    ),
    SiteConfig(
        id="youth_notices",
        name="校团委-通知公告",
        url="https://youth.qau.edu.cn/channel/tongzhigonggao",
        source="校团委",
        category="youth",
        audience=("student",),
    ),
    SiteConfig(
        id="youth_news",
        name="校团委-团学信息",
        url="https://youth.qau.edu.cn/channel/tuanxuexinxi",
        source="校团委",
        category="youth",
        audience=("student",),
    ),
    SiteConfig(
        id="jw_student",
        name="教务处-学生通知",
        url="https://jw.qau.edu.cn/channel/xstz",
        source="教务处",
        category="undergraduate_teaching",
        audience=("student",),
    ),
    SiteConfig(
        id="jw_teacher",
        name="教务处-教师通知",
        url="https://jw.qau.edu.cn/channel/jstz",
        source="教务处",
        category="teacher_teaching",
        audience=("teacher",),
    ),
    SiteConfig(
        id="hr_notices",
        name="人事处-通知公告",
        url="https://rsc.qau.edu.cn/channel/tzgg1",
        source="人事处",
        category="hr",
        audience=("teacher", "staff"),
    ),
    SiteConfig(
        id="graduate_notices",
        name="研究生处-通知公告",
        url="https://grad.qau.edu.cn/channel/tongzhigonggao",
        source="研究生处",
        category="graduate",
        audience=("graduate", "teacher"),
    ),
    SiteConfig(
        id="network_notices",
        name="网络信息管理处-通知公告",
        url="https://nc.qau.edu.cn/channel/tzgg",
        source="网络信息管理处",
        category="it",
        audience=("student", "teacher", "staff"),
    ),
    SiteConfig(
        id="student_affairs",
        name="学生工作处-通知",
        url="https://xgb.qau.edu.cn/channel/zxtz",
        source="学生工作处",
        category="student_affairs",
        audience=("student",),
    ),
)

