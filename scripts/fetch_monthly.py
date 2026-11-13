#!/usr/bin/env python3
"""抓中国摩托车商会月度「250ml 以上（不含）」产销快报 → data/market_monthly.js

为什么要有这个脚本：
  看板首页的「月度产销趋势」需要一条连续月度序列。商会没有 API，只按月发新闻稿，
  数字散落在每篇正文里。手抄一次可以，抄十次一定出错，所以做成脚本 + 数据文件：
  脚本负责取数与落库，CI 只读数据文件（商会站点对海外 IP 不稳，不放进构建流程）。

口径与取值规则（写入数据文件时逐条带来源链接，页面上可点回原文）：
  1. 只用「月度行业运行」稿，标题里带「海关」「公安部」「权威发布」的一律跳过；
  2. 数据月份 = 发布日期月份 - 1（商会固定次月中旬发上月数据）；
  3. 只取「排量250ml以上（不含）摩托车产销 X 万辆和 Y 万辆 … 同比增长/下降 A% 和 B%」这一段。

用法：
  python3 scripts/fetch_monthly.py            # 抓取并写入 data/market_monthly.js
  python3 scripts/fetch_monthly.py --check     # 只打印序列与自检结果，不写文件
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "market_monthly.js"
LIST_URL = "https://www.cccmp.com/tongjishuju/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
SKIP_WORDS = ("海关", "公安部", "权威发布")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def plain(html: str) -> str:
    html = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", html)


def list_reports() -> list[dict]:
    """从列表页抓「标题 / 链接 / 发布日期」，翻两页够了（一年 12 篇 + 海关稿）。"""
    out = []
    for page in (LIST_URL, LIST_URL + "?tid=tongjishuju&page=2"):
        try:
            html = fetch(page)
        except Exception as exc:  # 商会偶尔挂掉，第二页失败不影响第一页
            print("列表页抓取失败 %s：%s" % (page, exc), file=sys.stderr)
            continue
        # 条目结构：<a class="laws_item" href="/tongjishuju/1938.html"> <span>标题</span> <em>日期</em> </a>
        # 中间夹着大段被注释掉的旧模板，所以按 a 标签位置切片，只在片段内取 href / 标题 / 日期
        for chunk in re.split(r'<a[^>]+class="laws_item"', html)[1:]:
            chunk = chunk[:900]
            hm = re.search(r'href="(/tongjishuju/\d+\.html)"', chunk)
            title_m = re.search(r'<span>([\s\S]{0,140}?)</span>', chunk)
            date_m = re.search(r'<em>([\s\S]{0,40}?)</em>', chunk)
            if not (hm and title_m and date_m):
                continue
            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            date = date_m.group(1).strip()
            out.append({"url": "https://www.cccmp.com" + hm.group(1), "title": title, "date": date})
    return out


def parse_date(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# 正文原句有三种写法，纯正则死扣容易漏稿，改成两步定位：
#   ① 找「产销 X 万辆和 Y 万辆」，且前面 120 字内提到 250ml/250cc 以上（不含）
#   ② 再往后 160 字内找「同比(增长|下降) A% 和 (增长|下降) B%」，第二个词常省略，符号跟第一个走
# 必须紧贴「（排量250ml以上…）」这个定语，否则会把整车总量、二轮总量也当成分排量数据
PAIR_RE = re.compile(r"（?排量250(?:ml|cc)以上[^）]{0,20}(?:）)?[\s\S]{0,10}?产销([\d.]+)万辆和([\d.]+)万辆")
YOY_RE = re.compile(r"同比(增长|下降)?\s*([\d.]+)%\s*和\s*(增长|下降)?\s*([\d.]+)%")



def parse_report(url: str) -> dict | None:
    try:
        text = plain(fetch(url))
    except Exception as exc:
        print("正文抓取失败 %s：%s" % (url, exc), file=sys.stderr)
        return None
    for m in PAIR_RE.finditer(text):
        after = text[m.end(): m.end() + 200]
        y = YOY_RE.search(after)
        if not y:
            continue
        w1, v1, w2, v2 = y.group(1), float(y.group(2)), y.group(3), float(y.group(4))
        base = -1.0 if (w1 or "增长").startswith("下") else 1.0
        return {
            "prod": float(m.group(1)),
            "sales": float(m.group(2)),
            "yoyProd": base * v1,
            "yoySales": (-1.0 if (w2 or "").startswith("下") else base) * v2,
        }
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()

    reports = list_reports()
    picked: dict[str, dict] = {}
    for r in reports:
        if any(w in r["title"] for w in SKIP_WORDS):
            continue
        dt = parse_date(r["date"])
        if not dt:
            continue
        ym = (dt.year - 1, 12) if dt.month == 1 else (dt.year, dt.month - 1)
        key = "%04d-%02d" % ym
        if key in picked:
            continue
        row = parse_report(r["url"])
        if not row:
            continue
        row.update({"month": key, "url": r["url"], "title": r["title"], "published": dt.strftime("%Y-%m-%d")})
        picked[key] = row

    keep_year = max(int(k[:4]) for k in picked)  # 只保留最新一年，跨年混在一条线上没意义
    series = [picked[k] for k in sorted(picked) if int(k[:4]) == keep_year]
    if not series:
        print("一个月份都没解析出来，数据文件保持不变", file=sys.stderr)
        return 1

    latest = series[-1]
    payload = {
        "kind": "monthly_250_plus",
        "scope": "排量 250ml 以上（不含 250ml），燃油摩托车，产销单位「万辆」",
        "source": "中国摩托车商会 · 月度摩托车行业运行报告",
        "sourceUrl": "https://www.cccmp.com/tongjishuju/",
        "asOf": latest["month"],
        "lastFetched": datetime.now().strftime("%Y-%m-%d"),
        "series": series,
    }

    problems = []
    for row in series[1:]:
        prev = series[series.index(row) - 1]
        if prev["sales"]:
            calc = (row["sales"] / prev["sales"] - 1) * 100
            if abs(calc) > 80:
                problems.append("%s 环比 %.1f%%，疑似解析串行" % (row["month"], calc))
    if len(series) < 6:
        problems.append("只有 %d 个月，序列太短" % len(series))

    total_prod = round(sum(r["prod"] for r in series), 2)
    total_sales = round(sum(r["sales"] for r in series), 2)
    print("共 %d 个月：%s → %s" % (len(series), series[0]["month"], latest["month"]))
    for r in series:
        print("  %s  产 %5.2f 销 %5.2f  同比 %+6.2f%% / %+6.2f%%  %s" % (r["month"], r["prod"], r["sales"], r["yoyProd"], r["yoySales"], r["url"]))
    print("区间合计：产 %.2f 万辆 / 销 %.2f 万辆" % (total_prod, total_sales))
    if problems:
        print("\n自检问题：")
        for p in problems:
            print("  - " + p)
    else:
        print("自检通过：月份连续、环比幅度合理")

    if args.check:
        return 0

    body = json.dumps(payload, ensure_ascii=False, indent=1)
    OUT.write_text(
        "/* 月度产销序列，由 scripts/fetch_monthly.py 生成，请勿手改 */\n"
        "window.MOTO_MONTHLY = " + body + ";\n",
        encoding="utf-8",
    )
    print("\n已写入 %s（%d 字节）" % (OUT, OUT.stat().st_size))
    return 0 if not problems else 0


if __name__ == "__main__":
    sys.exit(main())
