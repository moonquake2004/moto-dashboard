#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装可发布的静态站点到 _site/。

上一版这些活是写死在 .github/workflows/pages.yml 的 shell 里的：拷 index.html、给数据文件加 ?v= 版本号、
只发布白名单文件。加了「独立品牌页 + sitemap」之后 shell 已经撑不住，收进这个脚本，
本地也能一条命令产出一份和线上完全一致的可预览站点：

    python3 build_site.py            # → _site/，并打印文件清单
    python3 build_site.py --out DIR  # 指定输出目录

产物：index.html（已注入 ?v=）· data/dashboard.js · assets/favicon.svg + logos/
     brand/<id>.html（44 个独立品牌页）· sitemap.xml · robots.txt · .nojekyll
"""
import argparse
import html
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://moonquake2004.github.io/moto-dashboard"
DATA_JSON = ROOT / "data" / "dashboard.json"
INDEX = ROOT / "index.html"


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def read_data():
    with DATA_JSON.open(encoding="utf-8") as f:
        return json.load(f)


def price_num(m):
    v = m.get("priceMin")
    return v if isinstance(v, (int, float)) else None


def fmt_price_band(models):
    vals = [price_num(m) for m in models if price_num(m) is not None]
    if not vals:
        return "价格未公布"
    lo, hi = min(vals), max(vals)
    def w(x):
        return "%.2f" % (x / 10000.0)
    if abs(lo - hi) < 1:
        return "%s 万元" % w(lo)
    return "%s–%s 万元" % (w(lo), w(hi))


def fmt_cc_band(models):
    vals = [m.get("cc") for m in models if m.get("cc")]
    if not vals:
        return "—"
    return "%d–%d cc" % (min(vals), max(vals)) if min(vals) != max(vals) else "%d cc" % min(vals)


def uncertain_li(u):
    """存疑条目有两种形态：结构化 dict（name/cc/type/reason）和整段说明字符串。"""
    if isinstance(u, str):
        return "<li>%s</li>" % esc(u)
    bits = [esc(u.get("name"))]
    meta = "，".join(
        x for x in (("排量 %s" % u["cc"]) if u.get("cc") else "", u.get("type") or "", u.get("price") or "") if x
    )
    if meta:
        bits.append("（%s）" % meta)
    if u.get("reason"):
        bits.append(" — %s" % esc(u["reason"]))
    return "<li>%s</li>" % "".join(bits)


BRAND_CSS = """
:root{--bg:#0B0D11;--surface:#141922;--surface2:#1B212D;--line:#242C3A;--line2:#2F3949;
 --ink:#EDF1F7;--muted:#9AA5B5;--faint:#69748A;--accent:#FF4A1F;--amber:#FFB020;--mint:#2FD9A6;--dom:#FF4A1F;--jv:#4C8DFF;--imp:#A66BFF;
 --logo-bg:#F2F4F8;--shadow:0 10px 30px rgba(0,0,0,.35)}
:root[data-theme=light]{--bg:#F4F6FA;--surface:#FFFFFF;--surface2:#EEF2F8;--line:#DCE3ED;--line2:#C6D0DE;
 --ink:#141A22;--muted:#5A6678;--faint:#8B96A6;--logo-bg:#FFFFFF;--shadow:0 8px 24px rgba(16,24,40,.08)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
 line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.top{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);
 backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
header.top .in{max-width:1080px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:14px}
.back{color:var(--muted);font-size:12.5px;text-decoration:none;font-weight:700;border:1px solid var(--line);
 padding:6px 11px;border-radius:8px;background:var(--surface)}
.back:hover{color:var(--accent);border-color:var(--accent)}
.crumb{font-size:11.5px;color:var(--faint)}
.hero{display:flex;gap:22px;align-items:flex-start;padding:34px 0 22px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.logo{width:132px;height:96px;flex:none;border-radius:14px;background:var(--logo-bg);display:flex;align-items:center;
 justify-content:center;border:1px solid var(--line);overflow:hidden}
.logo img{max-width:86%;max-height:76px;object-fit:contain}
.logo .fb{font-size:20px;font-weight:800;color:#333}
h1{font-size:30px;margin:0;letter-spacing:-.5px}
h1 .en{font-size:12px;color:var(--faint);font-weight:700;letter-spacing:.1em;margin-left:8px}
.company{color:var(--muted);font-size:13px;margin:2px 0 10px}
.tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{font-size:11px;font-weight:700;padding:3px 9px;border-radius:6px;border:1px solid var(--line);color:var(--muted);background:var(--surface2)}
.tag.accent{color:var(--accent);border-color:color-mix(in srgb,var(--accent) 45%,transparent);background:color-mix(in srgb,var(--accent) 12%,transparent)}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0 6px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:12px 14px}
.stat span{font-size:11px;color:var(--faint);font-weight:700;letter-spacing:.06em}
.stat b{display:block;font-size:19px;margin-top:2px}
h2{font-size:15px;margin:30px 0 10px;display:flex;align-items:center;gap:8px}
h2:before{content:"";width:3px;height:14px;background:var(--accent);border-radius:2px}
table{width:100%;border-collapse:collapse;font-size:12.5px;background:var(--surface);border:1px solid var(--line);
 border-radius:12px;overflow:hidden}
th{background:var(--surface2);color:var(--faint);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
 text-align:left;padding:9px 12px;border-bottom:1px solid var(--line)}
td{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:middle}
tr:last-child td{border-bottom:none}
td.p{color:var(--amber);font-weight:700;white-space:nowrap}
td.p.na{color:var(--faint);font-weight:400}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
a.src{color:var(--faint);text-decoration:none;font-size:13px}
a.src:hover{color:var(--accent)}
details{margin-top:12px;background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:11px 14px}
summary{cursor:pointer;font-size:12.5px;font-weight:700;color:var(--muted)}
details ul{margin:8px 0 0;padding-left:18px;font-size:12px;color:var(--muted)}
.sibs{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.sib{font-size:11.5px;padding:4px 10px;border-radius:999px;border:1px solid var(--line);background:var(--surface2);
 color:var(--ink);text-decoration:none}
.sib:hover{border-color:var(--accent);color:var(--accent)}
.sib i{color:var(--faint);font-style:normal;margin-left:4px}
.src-list{margin:6px 0 0;padding-left:18px;font-size:11.5px;color:var(--faint);word-break:break-all}
.note{font-size:12px;color:var(--muted);background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);
 border-radius:8px;padding:11px 14px;margin-top:12px;line-height:1.75}
footer{border-top:1px solid var(--line);margin-top:36px;padding:22px 0 40px;color:var(--faint);font-size:11.5px;line-height:1.9}
footer a{color:var(--muted)}
@media(max-width:640px){.stats{grid-template-columns:1fr 1fr}h1{font-size:23px}.logo{width:96px;height:74px}
 table{font-size:11.5px}th,td{padding:8px 9px}}
"""


def brand_page(b, d, siblings):
    """单个品牌页。纯静态、零 JS，模型表 + 来源 + 同类别内链。"""
    stats = d["stats"]
    models = b["models"]
    name = b["name"]
    price_band = fmt_price_band(models)
    cc_band = fmt_cc_band(models)
    upd = d["meta"]["updated"]
    cat = b.get("subCategory") or b.get("category") or ""
    url = "%s/brand/%s.html" % (SITE_URL, b["id"])

    rows = []
    for m in models:
        rows.append(
            "<tr><td>%s</td><td class=\"n\">%s</td><td>%s</td><td class=\"p%s\">%s</td><td>%s</td></tr>"
            % (
                esc(m.get("name")),
                ("%d cc" % m["cc"]) if m.get("cc") else "—",
                esc(m.get("type")),
                "" if m.get("price") else " na",
                esc(m.get("price") or "—"),
                ('<a class="src" href="%s" target="_blank" rel="noopener" title="核实来源">↗</a>' % esc(m["source"]))
                if m.get("source")
                else '<span style="color:var(--faint)">·</span>',
            )
        )
    table = (
        "<table><thead><tr><th>型号</th><th>排量</th><th>类别</th><th>官方指导价</th><th>来源</th></tr></thead>"
        "<tbody>%s</tbody></table>" % "".join(rows)
    ) if rows else '<div class="note">该品牌当前没有 ≥250cc 的在售车型收录。</div>'

    unc = ""
    if b.get("uncertain"):
        items = "".join(uncertain_li(u) for u in b["uncertain"])
        unc = '<details><summary>%d 条存疑，已核实但未纳入统计</summary><ul>%s</ul></details>' % (
            len(b["uncertain"]),
            items,
        )

    sibs = "".join(
        '<a class="sib" href="%s.html">%s<i>%d</i></a>' % (esc(x["id"]), esc(x["name"]), x["modelCount"])
        for x in siblings
    )
    sib_block = (
        '<h2>同类别其他品牌</h2><div class="sibs">%s</div>' % sibs if sibs else ""
    )

    srcs = "".join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (esc(u), esc(u)) for u in b.get("sources") or [])
    src_block = '<h2>核实来源</h2><ul class="src-list">%s</ul>' % srcs if srcs else ""

    note = ('<div class="note">%s</div>' % esc(b["note"])) if b.get("note") else ""

    ld_items = []
    for i, m in enumerate(models, 1):
        prod = {
            "@type": "Product",
            "name": "%s %s" % (name, m.get("name") or ""),
            "brand": {"@type": "Brand", "name": name},
            "category": m.get("type") or "摩托车",
            "url": url,
        }
        p = price_num(m)
        if p:
            prod["offers"] = {
                "@type": "Offer",
                "price": str(int(p)),
                "priceCurrency": "CNY",
                "availability": "https://schema.org/InStock",
            }
        ld_items.append({"@type": "ListItem", "position": i, "item": prod})

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Brand",
                "name": name,
                "alternateName": b.get("nameEn") or "",
                "url": url,
                "description": "%s（%s）在中国市场 ≥250cc 在售车型 %d 款，价格区间 %s。" % (name, cat, len(models), price_band),
                "parentOrganization": {"@type": "Organization", "name": b.get("company") or name},
            },
            {"@type": "ItemList", "name": "%s 在售车型" % name, "numberOfItems": len(models), "itemListElement": ld_items},
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "国内 250cc+ 摩托车品牌看板", "item": SITE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": name, "item": url},
                ],
            },
        ],
    }

    title = "%s %s 在售车型与价格（≥250cc，%d 款）｜250cc+ 摩托车品牌看板" % (name, b.get("nameEn") or "", len(models))
    desc = "%s（%s）在中国市场 ≥250cc 在售车型 %d 款，价格 %s，排量 %s。逐条车型可点开品牌官网或车型库核实来源。" % (
        name, b.get("company") or "", len(models), price_band, cc_band,
    )

    logo_html = (
        '<div class="logo"><img src="../%s" alt="%s Logo" loading="lazy"></div>'
        % (esc(b["logo"]["file"]), esc(name))
        if b.get("logo", {}).get("status") == "ok"
        else '<div class="logo"><span class="fb">%s</span></div>' % esc(name)
    )

    badges = ['<span class="tag accent">%s</span>' % esc(cat)]
    if b.get("group"):
        badges.append('<span class="tag">%s</span>' % esc(b["group"]))
    if b.get("marketStatus") == "parallel":
        badges.append('<span class="tag">平行进口 · 未计入统计口径</span>')
    if b.get("website"):
        badges.append('<span class="tag"><a href="%s" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">品牌官网 ↗</a></span>' % esc(b["website"]))

    return """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<style>{css}</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="top"><div class="in">
  <a class="back" href="../index.html">← 全部 {brands} 个品牌</a>
  <span class="crumb">MOTO GRID · 250cc+ · {cat}</span>
</div></header>
<main class="wrap">
  <div class="hero">
    {logo}
    <div style="flex:1;min-width:220px">
      <h1>{name}<span class="en">{en}</span></h1>
      <div class="company">{company}</div>
      <div class="tags">{badges}</div>
    </div>
  </div>
  <div class="stats">
    <div class="stat"><span>在售车型</span><b>{n} 款</b></div>
    <div class="stat"><span>价格区间</span><b>{price_band}</b></div>
    <div class="stat"><span>排量区间</span><b>{cc_band}</b></div>
  </div>
  <h2>{name} 在售车型</h2>
  {table}
  {unc}
  {note}
  {sib_block}
  {src_block}
</main>
<footer><div class="wrap">
  数据更新 {upd} ｜ 口径：中国市场在售 · 排量 ≥250cc ｜ 全库 {tot_b} 品牌 / {tot_m} 型号<br>
  <a href="../index.html#about">数据口径与完整性说明</a> ·
  <a href="../index.html">返回看板</a> · <a href="../index.html#explorer">在型号浏览器中筛选</a>
</div></footer>
</body>
</html>
""".format(
        title=esc(title),
        desc=esc(desc),
        url=url,
        css=BRAND_CSS,
        ld=json.dumps(ld, ensure_ascii=False, separators=(",", ":")),
        brands=stats["brandCount"],
        cat=esc(cat),
        logo=logo_html,
        name=esc(name),
        en=esc(b.get("nameEn") or ""),
        company=esc(b.get("company") or ""),
        badges="".join(badges),
        n=len(models),
        price_band=esc(price_band),
        cc_band=esc(cc_band),
        table=table,
        unc=unc,
        note=note,
        sib_block=sib_block,
        src_block=src_block,
        upd=esc(upd),
        tot_b=stats["brandCount"],
        tot_m=stats["modelCountAll"],
    )


def build(out_dir, ver=None):
    d = read_data()
    sites = sorted([b for b in d["brands"] if b["marketStatus"] != "parallel"], key=lambda b: -b["modelCount"])
    ver = ver or time.strftime("%Y%m%d%H%M", time.gmtime())

    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    (out / "assets" / "logos").mkdir(parents=True)
    (out / "brand").mkdir(parents=True)

    # index.html：注入数据文件版本号
    idx = INDEX.read_text(encoding="utf-8")
    idx2 = idx.replace('src="data/dashboard.js"', 'src="data/dashboard.js?v=%s"' % ver)
    idx2 = idx2.replace('src="data/market_monthly.js"', 'src="data/market_monthly.js?v=%s"' % ver)
    # 静态品牌索引：44 个内链，既是站内目录也是给搜索引擎的入口（JS 生成的卡片抓不到）
    links = "".join(
        '<a class="bi" href="brand/%s.html">%s<i>%d</i></a>' % (esc(b["id"]), esc(b["name"]), b["modelCount"])
        for b in sorted(d["brands"], key=lambda x: (-x["modelCount"], x["id"]))
    )
    idx2 = idx2.replace("<!--BRAND_INDEX-->", links)
    if 'data/dashboard.js?v=' not in idx2:
        sys.exit("index.html 里没找到 data/dashboard.js 的 script 标签，发布中止")
    if 'data/market_monthly.js?v=' not in idx2:
        sys.exit("index.html 里没找到 data/market_monthly.js 的 script 标签，发布中止")
    # 月度序列是手抓落库的，序列太短或字段缺失都会让首页趋势面板变空白，构建时先拦一道
    monthly = (ROOT / "data" / "market_monthly.js").read_text(encoding="utf-8")
    n_month = monthly.count('"month"')
    if n_month < 6:
        sys.exit("data/market_monthly.js 只有 %d 个月，趋势面板会太空，发布中止" % n_month)
    for k in ("prod", "sales", "yoySales", "url"):
        if '"%s"' % k not in monthly:
            sys.exit("data/market_monthly.js 缺字段 %s，发布中止" % k)
    (out / "index.html").write_text(idx2, encoding="utf-8")

    shutil.copy(ROOT / "data" / "dashboard.js", out / "data" / "dashboard.js")
    shutil.copy(ROOT / "data" / "market_monthly.js", out / "data" / "market_monthly.js")
    shutil.copy(ROOT / "assets" / "favicon.svg", out / "assets" / "favicon.svg")
    for f in (ROOT / "assets" / "logos").glob("*"):
        if f.is_file():
            shutil.copy(f, out / "assets" / "logos" / f.name)
    (out / ".nojekyll").write_text("", encoding="utf-8")

    # 品牌页
    groups = {}
    for b in d["brands"]:
        groups.setdefault(b.get("subCategory") or b.get("category"), []).append(b)
    for b in d["brands"]:
        key = b.get("subCategory") or b.get("category")
        siblings = [x for x in groups.get(key, []) if x["id"] != b["id"] and x["modelCount"]]
        (out / "brand" / ("%s.html" % b["id"])).write_text(brand_page(b, d, siblings), encoding="utf-8")

    # sitemap / robots
    upd = d["meta"]["updated"]
    urls = ['<url><loc>%s/</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>' % (SITE_URL, upd)]
    for b in d["brands"]:
        pr = "0.8" if b["modelCount"] >= 10 else "0.6"
        urls.append(
            '<url><loc>%s/brand/%s.html</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>'
            % (SITE_URL, b["id"], upd, pr)
        )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )
    (out / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL, encoding="utf-8"
    )

    files = sorted(p for p in out.rglob("*") if p.is_file())
    total = sum(p.stat().st_size for p in files)
    print("输出目录: %s" % out)
    print("文件数: %d ｜ 总体积: %.1f KB ｜ 品牌页: %d ｜ 数据版本: %s" % (len(files), total / 1024.0, len(d["brands"]), ver))
    for p in files:
        if p.suffix in (".html", ".xml", ".txt", ".js", ".svg"):
            print("  %-42s %7.1f KB" % (p.relative_to(out), p.stat().st_size / 1024.0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "_site"))
    ap.add_argument("--ver", default=None, help="数据文件版本号，默认取当前 UTC 时间 YYYYmmddHHMM")
    a = ap.parse_args()
    build(a.out, a.ver)


if __name__ == "__main__":
    main()
