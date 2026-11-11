# -*- coding: utf-8 -*-
"""
moto-dashboard 访问统计后端（Flask + SQLite）

功能：
  1. /api/visit  POST  —— 前端上报一次访问，记录 IP / 地区 / 设备 / OS / 浏览器 / 时间 / 来源
  2. /api/stats  GET   —— 返回计数器数据（总 PV、24h 独立访客、累计独立访客）
  3. /admin      GET   —— 后台查看页（需 ?token=ADMIN_TOKEN），展示访客明细

设计要点：
  * 纯静态 GitHub Pages 无法记录访客，本服务承担"服务端存储"。
  * 按 IP 去重：同一 IP 在 24h 窗口内只计 1 个独立访客（UV）。
  * 地区查询默认用 ip-api.com（免费、无需 key、支持中文）；
    国内网络若访问不稳，可改用本地 ip2region 库（见 geo_lookup 注释）。
  * 跨域：after_request 统一加 CORS，ALLOW_ORIGIN 设为 GitHub Pages 域名即可。
  * 鉴权：/admin 用 ADMIN_TOKEN 保护，避免公开泄露访客隐私。

部署（CloudStudio / 任意能跑 Python 的机器）：
  pip install -r requirements.txt
  ADMIN_TOKEN=你的口令 PORT=5000 ALLOW_ORIGIN=https://moonquake2004.github.io python stats_server.py
"""
import os
import json
import sqlite3
import datetime
import urllib.request
from flask import Flask, request, jsonify, abort, Response

try:
    from user_agents import parse as ua_parse
except Exception:
    ua_parse = None

app = Flask(__name__)

DB = os.environ.get("STATS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.db"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "changeme")
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "*")
PORT = int(os.environ.get("PORT", "5000"))
GEO_TIMEOUT = 5


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS visits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT, country TEXT, region TEXT, city TEXT,
        device TEXT, os TEXT, browser TEXT,
        ua TEXT, referer TEXT, path TEXT, ts TEXT)""")
    conn.commit()
    conn.close()


def get_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def is_private(ip):
    return (ip in ("127.0.0.1", "::1", "unknown")
            or ip.startswith("192.168.") or ip.startswith("10.")
            or ip.startswith("172.16.") or ip.startswith("172.17.")
            or ip.startswith("172.18.") or ip.startswith("172.19.")
            or ip.startswith("172.2") or ip.startswith("172.3")
            or ip.startswith("::ffff:127."))


def geo_lookup(ip):
    """返回 (country, region, city)。默认 ip-api.com；内网/失败降级为空。

    若需完全离线、国内精确，可改为 ip2region：
        from ip2region import xdb
        db = xdb.XdbSearcher(content=bytes.fromhex(...))  # 载入 xdb 文件
        region = db.search(ip)  # 返回 "国家|省|市|运营商"
    把下面这段替换即可，其余逻辑不变。
    """
    if is_private(ip):
        return ("本地", "本地", "本地")
    try:
        url = "https://ip-api.com/json/%s?lang=zh-CN&fields=country,regionName,city" % ip
        req = urllib.request.Request(url, headers={"User-Agent": "moto-stats"})
        with urllib.request.urlopen(req, timeout=GEO_TIMEOUT) as r:
            d = json.loads(r.read().decode())
        if d.get("status") == "success":
            return (d.get("country", ""), d.get("regionName", ""), d.get("city", ""))
    except Exception:
        pass
    return ("", "", "")


def parse_ua(ua_str):
    if not ua_parse:
        return ("unknown", "unknown", "unknown")
    try:
        ua = ua_parse(ua_str)
        device = "mobile" if ua.is_mobile else ("tablet" if ua.is_tablet else "desktop")
        return (device, ua.os.family, ua.browser.family)
    except Exception:
        return ("unknown", "unknown", "unknown")


DEVICE_CN = {"mobile": "手机", "tablet": "平板", "desktop": "电脑", "unknown": "未知"}


@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = ALLOW_ORIGIN
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/api/visit", methods=["POST", "OPTIONS"])
def visit():
    if request.method == "OPTIONS":
        return "", 204
    ua_str = request.headers.get("User-Agent", "")
    device, os_name, browser = parse_ua(ua_str)
    ip = get_client_ip()
    country, region, city = geo_lookup(ip)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    data = request.get_json(silent=True) or {}
    path = data.get("path", request.path)
    referer = request.referrer or data.get("referer", "") or ""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO visits(ip,country,region,city,device,os,browser,ua,referer,path,ts)"
                  " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (ip, country, region, city, device, os_name, browser, ua_str, referer, path, ts))
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True}), 200


@app.route("/api/stats")
def stats():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visits")
    pv = c.fetchone()[0]
    window = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("SELECT COUNT(DISTINCT ip) FROM visits WHERE ts >= ?", (window,))
    uv24 = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT ip) FROM visits")
    uv_all = c.fetchone()[0]
    conn.close()
    return jsonify({"pv": pv, "uv24": uv24, "uv_all": uv_all})


ADMIN_HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>访问统计后台</title>
<style>
body{font-family:-apple-system,"PingFang SC",Segoe UI,sans-serif;background:#f5f7fa;margin:0;padding:20px;color:#1a1a1a}
h1{font-size:18px;margin:0 0 14px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.card{background:#fff;border:1px solid #e3e8ef;border-radius:10px;padding:14px 18px;min-width:120px}
.card b{display:block;font-size:26px;color:#c1121f}
.card span{font-size:12px;color:#7a8696}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e3e8ef;border-radius:10px;overflow:hidden;font-size:12.5px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #eef1f5}
th{background:#fafbfc;color:#5b6675;font-weight:600}
tr:hover td{background:#f8fafc}
.tag{padding:1px 7px;border-radius:5px;font-size:11px;background:#eef2f7;color:#566}
</style></head><body>
<h1>访问统计后台</h1>
<div class="cards">
  <div class="card"><b>{{pv}}</b><span>总访问人次 PV</span></div>
  <div class="card"><b>{{uv24}}</b><span>近 24h 独立访客</span></div>
  <div class="card"><b>{{uv_all}}</b><span>累计独立访客</span></div>
</div>
<table><thead><tr>
  <th>#</th><th>IP</th><th>地区</th><th>设备</th><th>系统</th><th>浏览器</th><th>来源</th><th>路径</th><th>时间(UTC)</th>
</tr></thead><tbody>
{% for r in rows %}
<tr><td>{{loop.index}}</td><td>{{r[0]}}</td>
<td>{{r[1]}}{% if r[2] %}·{{r[2]}}{% endif %}{% if r[3] %}·{{r[3]}}{% endif %}</td>
<td><span class="tag">{{r[4]}}</span></td><td>{{r[5]}}</td><td>{{r[6]}}</td>
<td>{{r[8][:40]}}</td><td>{{r[7]}}</td><td>{{r[9]}}</td></tr>
{% endfor %}
</tbody></table>
</body></html>"""


@app.route("/admin")
def admin():
    token = request.args.get("token", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        abort(401)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT ip,country,region,city,device,os,browser,path,referer,ts FROM visits ORDER BY id DESC LIMIT 200")
    rows = c.fetchall()
    c.execute("SELECT COUNT(*) FROM visits")
    pv = c.fetchone()[0]
    window = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("SELECT COUNT(DISTINCT ip) FROM visits WHERE ts >= ?", (window,))
    uv24 = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT ip) FROM visits")
    uv_all = c.fetchone()[0]
    conn.close()
    # 设备转中文
    rows = [list(r) for r in rows]
    for r in rows:
        r[4] = DEVICE_CN.get(r[4], r[4])
    try:
        from flask import render_template_string
        return render_template_string(ADMIN_HTML, rows=rows, pv=pv, uv24=uv24, uv_all=uv_all)
    except Exception:
        # 无 Jinja 时降级为纯文本表格
        txt = "PV=%s UV24=%s UVall=%s\n" % (pv, uv24, uv_all)
        for r in rows:
            txt += " | ".join(str(x) for x in r) + "\n"
        return Response(txt, mimetype="text/plain; charset=utf-8")


@app.route("/")
def index():
    return jsonify({"service": "moto-dashboard stats", "endpoints": ["/api/visit", "/api/stats", "/admin"]})


if __name__ == "__main__":
    init_db()
    print("stats_server listening on :%d  (admin token=%s)" % (PORT, ADMIN_TOKEN))
    app.run(host="0.0.0.0", port=PORT, debug=False)
