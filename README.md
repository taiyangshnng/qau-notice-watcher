# qau-notice-watcher

青岛农业大学公开通知频道每日监控器。项目每天低频抓取多个官方列表页，筛选新增通知，写入 SQLite 去重库，生成 `daily.md` 与 `crawl_log.json`，并可在每次正常运行后发送邮件。

## 监控频道

- 学校官网-通知公告
- 校团委-通知公告
- 校团委-团学信息
- 教务处-学生通知
- 教务处-教师通知
- 人事处-通知公告
- 研究生处-通知公告
- 网络信息管理处-通知公告
- 学生工作处-通知

频道配置集中在 `sites.py`。如果页面能访问但解析数量为 0，优先检查 `parser.py`。

## 本地运行

建议使用 Python 3.11 或更新版本。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

运行后会生成：

- `daily.md`：本次新增通知摘要
- `reports/YYYY-MM-DD.md`：按日期保存的历史摘要
- `crawl_log.json`：每个频道的抓取状态、HTTP 状态码、解析数量、错误信息和邮件状态
- `data/seen.sqlite`：已经见过的通知链接，用于去重

## 第一次初始化

第一次运行建议先建立基线，避免把列表页已有通知全部当成新增通知。

```bash
python main.py --init
```

之后每天正常运行：

```bash
python main.py
```

如果只是想看看“当前网页列表里能解析到哪些通知”，不想影响去重库，可以运行：

```bash
python main.py --preview
```

如果本次运行不想发邮件，可以运行：

```bash
python main.py --no-mail
```

如果只想更新最新摘要、不保存历史文件，可以运行：

```bash
python main.py --no-archive
```

## 自动运行

`.github/workflows/daily.yml` 会：

- 每天北京时间 8:00 自动运行
- 支持在 Actions 页面手动运行
- 安装依赖后执行 `python main.py`
- 邮件配置完整时，每次正常运行都会发送 `daily.md`
- 每天额外保存一份 `reports/YYYY-MM-DD.md`
- 如果 `daily.md`、`reports/`、`crawl_log.json`、`data/seen.sqlite` 有变化，自动提交回仓库

手动触发路径：

```text
GitHub 仓库 -> Actions -> QAU Daily Notice Watcher -> Run workflow
```

## 历史摘要规则

`daily.md` 始终显示最近一次运行结果。`reports/YYYY-MM-DD.md` 用来保存当天历史摘要：

- 当天第一次有新增通知时，写入当天历史文件
- 同一天后续运行没有新增通知时，不覆盖当天历史文件
- 同一天后续运行又发现新增通知时，追加到当天历史文件末尾，并用 `---` 分隔

这样手动重复运行不会把已经保存的当天通知覆盖成“暂无新增通知”。

## 邮件推送

邮件推送通过 GitHub Secrets 配置，不要把邮箱密码写进代码。

在 GitHub 仓库页面进入：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

添加这些 secret：

- `SMTP_HOST`：SMTP 服务器地址，例如 `smtp.qq.com`
- `SMTP_PORT`：SMTP 端口，常用 `465` 或 `587`
- `SMTP_USER`：发件邮箱账号
- `SMTP_PASSWORD`：邮箱 SMTP 授权码或应用专用密码
- `MAIL_TO`：收件邮箱，可以写多个，用英文逗号分隔
- `SMTP_SSL`：可选。端口 465 可填 `true`，端口 587 可不填

常见邮箱提示：

- QQ 邮箱通常使用 `smtp.qq.com`、端口 `465`、`SMTP_SSL=true`
- 163 邮箱通常使用 `smtp.163.com`、端口 `465`、`SMTP_SSL=true`
- Gmail 通常需要应用专用密码

如果这些配置不完整，程序会跳过邮件发送，但爬虫和报告仍会正常运行。正常运行 `python main.py` 时，无论当天是否有新增通知，都会尝试发送 `daily.md`；初始化模式和预览模式不会发送邮件。

## 标签规则

`classifier.py` 会按标题关键词自动标记：

- `activity`
- `competition`
- `volunteer`
- `academic`
- `exam`
- `scholarship`
- `employment`
- `hr`
- `it_notice`
- `admin`
- `other`

## 安全与合规抓取策略

- 每天只运行一次
- 默认只抓公开列表页
- 不抓登录后内容
- 不绕过权限
- 不并发请求
- 每个请求之间随机等待 3-8 秒
- 请求超时时间 10 秒
- 失败最多重试 1 次
- 遇到 403、429、5xx 跳过，不反复请求
- 不采集个人敏感信息
- 仅用于个人学习和校园通知聚合
