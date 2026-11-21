# -*- coding: utf-8 -*-
"""
moto-dashboard 访问统计后端（Flask + SQLite）

功能：
  1. /api/visit  POST  —— 前端上报一次访问，记录 IP / 地区 / 设备 / OS / 浏览器 / 时间 / 来源
  2. /api/stats  GET   —— 返回计数器数据（累计访问、24h 独立访客、累计独立访客）
  3. /admin      GET   —— 后台查看页（token 鉴权），展示访客明细

设计要点：
  * 纯静态 GitHub Pages 无法记录访客，本服务承担"服务端存储"。
  * 同一 IP 60s 内只落一条记录（既防刷，也让 PV 接近真实访问数）。
  * 入库的 IP 默认截断；UV 按带盐哈希去重，明细按 RETAIN_DAYS 自动清理。
  * 归属地为**异步补写**：/api/visit 先落库立即返回，再由后台线程查
    ip-api.com（免费版只支持 http，且限速 45 次/分钟，故带 6 小时缓存）。
  * 默认不开 CORS，必须显式设置 ALLOW_ORIGIN 才会输出跨域头。
  * /admin 必须设置 ADMIN_TOKEN 环境变量，否则服务拒绝启动；口令只认 X-Admin-Token 请求头。

部署（CloudStudio / 任意能跑 Python 的机器）：
  pip install -r requirements.txt gunicorn
  export ADMIN_TOKEN=$(openssl rand -hex 16) IP_SALT=$(openssl rand -hex 16)
  export ALLOW_ORIGIN=https://moonquake2004.github.io
  gunicorn -w 2 --threads 4 -b 0.0.0.0:5000 --access-logfile - stats_server:app
  # 放在 nginx 等反代后面时加 TRUST_PROXY=1；本地调试可直接 python stats_server.py（只监听 127.0.0.1）

隐私相关环境变量：
  IP_MODE=truncate|hash|full   默认 truncate（IPv4 抹最后一段 / IPv6 留 /48）
  IP_SALT                      UV 去重用的哈希盐，默认复用 ADMIN_TOKEN；生产建议单独设置
  RETAIN_DAYS=180              明细保留天数，0 = 不清理
  ALLOW_TOKEN_QUERY=1          允许 /admin?token= 方式（默认关闭，只认 X-Admin-Token 头）
"""
import datetime
import hashlib
import hmac
import ipaddress
import json
import os
import sqlite3
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, Response, abort, jsonify, render_template_string, request

try:
    from user_agents import parse as ua_parse
except Exception:
    ua_parse = None

app = Flask(__name__)

DB = os.environ.get("STATS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.db"))

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "").strip()
if not ADMIN_TOKEN:
    # 不静默使用默认口令：默认部署等于把访客 IP 公开
    raise SystemExit("请先设置 ADMIN_TOKEN 环境变量（例如 ADMIN_TOKEN=$(openssl rand -hex 16)）")

# 留空 = 不输出 CORS 头（默认最安全）；部署时填前端域名，如 https://xxx.github.io
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "").strip()
TRUST_PROXY = os.environ.get("TRUST_PROXY", "").strip() in ("1", "true", "yes")
GEO_ENABLE = os.environ.get("GEO_ENABLE", "1").strip() not in ("0", "false", "no")
GEO_TIMEOUT = 2          # 归属地查询超时（秒），失败就当没查到
GEO_TTL = 6 * 3600       # 同一 IP 的归属地缓存时间
RATE_WINDOW = 60         # 同一 IP 的落库间隔（秒）
PORT = int(os.environ.get("PORT", "5000"))
# 隐私：默认只存截断后的 IP（IPv4 抹最后一段、IPv6 只留 /48），UV 用加盐哈希去重
IP_MODE = os.environ.get("IP_MODE", "truncate").strip()        # truncate | hash | full
IP_SALT = os.environ.get("IP_SALT", "").strip() or ADMIN_TOKEN   # 换盐 = 历史 UV 不再可关联
RETAIN_DAYS = int(os.environ.get("RETAIN_DAYS", "180"))          # 访问明细保留天数，0 = 不清理
ALLOW_TOKEN_QUERY = os.environ.get("ALLOW_TOKEN_QUERY", "").strip() in ("1", "true", "yes")
DISPLAY_TZ = datetime.timezone(datetime.timedelta(hours=8))      # 后台按北京时间显示
GEO_POOL = ThreadPoolExecutor(max_workers=int(os.environ.get("GEO_WORKERS", "2")), thread_name_prefix="geo")
_geo_pending = threading.BoundedSemaphore(int(os.environ.get("GEO_QUEUE", "200")))

DEVICE_CN = {"mobile": "手机", "tablet": "平板", "desktop": "电脑", "unknown": "未知"}


# ------------------------------------------------------------------ 数据库

def init_db():
    conn = sqlite3.connect(DB, timeout=10)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS visits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT, country TEXT, region TEXT, city TEXT,
        device TEXT, os TEXT, browser TEXT,
        ua TEXT, referer TEXT, path TEXT, ts TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_visits_ts ON visits(ts)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_visits_ip ON visits(ip)")
    cols = {r[1] for r in c.execute("PRAGMA table_info(visits)")}
    if "ip_hash" not in cols:      # 旧库平滑升级：老数据用原 ip 字段兜底去重
        c.execute("ALTER TABLE visits ADD COLUMN ip_hash TEXT")
        c.execute("UPDATE visits SET ip_hash = ip WHERE ip_hash IS NULL")
    c.execute("CREATE INDEX IF NOT EXISTS idx_visits_iph ON visits(ip_hash)")
    conn.commit()
    conn.close()


def connect():
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ------------------------------------------------------------- 请求信息

def _safe_ip(text):
    try:
        return ipaddress.ip_address(text)
    except (ValueError, TypeError):
        return None


def is_private(ip):
    """私有 / 回环 / 链路本地地址。用 ipaddress 判断，别再手写前缀匹配。"""
    addr = _safe_ip(ip)
    if addr is None:
        return True
    return addr.is_private or addr.is_loopback or addr.is_link_local


def get_client_ip():
    peer = request.remote_addr or "unknown"
    xff = request.headers.get("X-Forwarded-For", "")
    # 只有在本机 / 内网代理转发（或显式 TRUST_PROXY）时才信 XFF，否则可被任意伪造
    if xff and (TRUST_PROXY or is_private(peer)):
        first = xff.split(",")[0].strip()
        if _safe_ip(first):
            return first
    return peer


def mask_ip(ip):
    """按 IP_MODE 处理入库的 IP：truncate 抹掉主机位，hash 只存哈希，full 原样（需自行承担合规）。"""
    addr = _safe_ip(ip)
    if addr is None:
        return "unknown"
    if IP_MODE == "full":
        return str(addr)
    if IP_MODE == "hash":
        return "h:" + ip_hash(ip)[:16]
    net = ipaddress.ip_network("%s/%d" % (addr, 24 if addr.version == 4 else 48), strict=False)
    return str(net.network_address) + ("/24" if addr.version == 4 else "/48")


def ip_hash(ip):
    """带盐 HMAC：同一访客稳定、不可逆；只用来数 UV，不用于展示。"""
    return hmac.new(IP_SALT.encode(), str(ip).encode(), hashlib.sha256).hexdigest()


def parse_ua(ua_str):
    if not ua_parse:
        return ("unknown", "unknown", "unknown")
    try:
        ua = ua_parse(ua_str)
        device = "mobile" if ua.is_mobile else ("tablet" if ua.is_tablet else "desktop")
        return (device, ua.os.family, ua.browser.family)
    except Exception:
        return ("unknown", "unknown", "unknown")


# --------------------------------------------------------------- 归属地

_geo_cache = {}
_geo_lock = threading.Lock()


def geo_lookup(ip):
    """返回 (country, region, city)。内网直接返回「本地」，失败返回空。"""
    if is_private(ip):
        return ("本地", "本地", "本地")
    if not GEO_ENABLE:
        return ("", "", "")
    now = time.time()
    with _geo_lock:
        hit = _geo_cache.get(ip)
        if hit and hit[0] > now:
            return hit[1]
    try:
        # 注意：ip-api.com 免费版只支持 http，https 是 Pro 才有的
        url = "http://ip-api.com/json/%s?lang=zh-CN&fields=status,country,regionName,city" % ip
        req = urllib.request.Request(url, headers={"User-Agent": "moto-stats"})
        with urllib.request.urlopen(req, timeout=GEO_TIMEOUT) as r:
            d = json.loads(r.read().decode())
        if d.get("status") == "success":
            val = (d.get("country", ""), d.get("regionName", ""), d.get("city", ""))
            with _geo_lock:
                if len(_geo_cache) > 5000:
                    _geo_cache.clear()
                _geo_cache[ip] = (now + GEO_TTL, val)
            return val
    except Exception:
        pass
    return ("", "", "")


def _enrich(row_id, ip):
    try:
        _enrich_inner(row_id, ip)
    finally:
        _geo_pending.release()


def _enrich_inner(row_id, ip):
    country, region, city = geo_lookup(ip)
    if not (country or region or city):
        return
    try:
        conn = connect()
        conn.execute("UPDATE visits SET country=?,region=?,city=? WHERE id=?",
                     (country, region, city, row_id))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------- 限流

_rate = {}
_rate_lock = threading.Lock()


def rate_limited(ip):
    now = time.time()
    with _rate_lock:
        last = _rate.get(ip, 0)
        if now - last < RATE_WINDOW:
            return True
        _rate[ip] = now
        if len(_rate) > 2000:
            for k, v in list(_rate.items()):
                if now - v > RATE_WINDOW * 10:
                    _rate.pop(k, None)
    return False


# ---------------------------------------------------------------- 路由

@app.after_request
def add_headers(resp):
    if ALLOW_ORIGIN:
        resp.headers["Access-Control-Allow-Origin"] = ALLOW_ORIGIN
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Vary"] = "Origin"
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    if request.path.startswith("/admin"):
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/visit", methods=["POST", "OPTIONS"])
def visit():
    if request.method == "OPTIONS":
        return "", 204
    ip = get_client_ip()
    purge_old()
    if rate_limited(ip):
        return jsonify({"ok": True, "skipped": "rate"}), 200

    ua_str = (request.headers.get("User-Agent", "") or "")[:300]
    device, os_name, browser = parse_ua(ua_str)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    data = request.get_json(silent=True) or {}
    path = str(data.get("path") or request.path)[:200]
    # 来源只留 scheme+host+path，丢掉 query（里面常带搜索词、token 等个人信息）
    referer = str(request.referrer or data.get("referer") or "")
    referer = referer.split("?", 1)[0].split("#", 1)[0][:300]

    try:
        conn = connect()
        c = conn.cursor()
        c.execute("INSERT INTO visits(ip,ip_hash,country,region,city,device,os,browser,ua,referer,path,ts)"
                  " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (mask_ip(ip), ip_hash(ip), "", "", "", device, os_name, browser, ua_str, referer, path, ts))
        row_id = c.lastrowid
        conn.commit()
        conn.close()
    except Exception:
        app.logger.exception("visit insert failed")
        return jsonify({"ok": False}), 500   # 不把异常文本回给客户端

    # 归属地异步补写走固定大小线程池；队列满就放弃这次补写，避免被刷时线程数暴涨
    if GEO_ENABLE and not is_private(ip) and _geo_pending.acquire(blocking=False):
        try:
            GEO_POOL.submit(_enrich, row_id, ip)
        except RuntimeError:
            _geo_pending.release()
    return jsonify({"ok": True}), 200


def _counters(conn=None):
    own = conn is None
    conn = conn or connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visits")
    pv = c.fetchone()[0]
    window = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("SELECT COUNT(DISTINCT ip_hash) FROM visits WHERE ts >= ?", (window,))
    uv24 = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT ip_hash) FROM visits")
    uv_all = c.fetchone()[0]
    if own:
        conn.close()
    return pv, uv24, uv_all


_last_purge = [0.0]


def purge_old():
    """按 RETAIN_DAYS 清理明细，最多每小时跑一次。"""
    if RETAIN_DAYS <= 0 or time.time() - _last_purge[0] < 3600:
        return
    _last_purge[0] = time.time()
    cut = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=RETAIN_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = connect()
        conn.execute("DELETE FROM visits WHERE ts < ?", (cut,))
        conn.commit()
        conn.close()
    except Exception:
        app.logger.exception("purge failed")


@app.route("/api/stats")
def stats():
    try:
        pv, uv24, uv_all = _counters()
    except Exception:
        app.logger.exception("stats failed")
        return jsonify({"pv": 0, "uv24": 0, "uv_all": 0}), 503
    return jsonify({"pv": pv, "uv24": uv24, "uv_all": uv_all})


def admin_ok():
    """口令只认请求头：放在 URL 里会进浏览器历史、代理与服务器访问日志。
    确实需要用浏览器直接打开时，可设 ALLOW_TOKEN_QUERY=1 临时放开。"""
    tok = request.headers.get("X-Admin-Token") or ""
    if not tok and ALLOW_TOKEN_QUERY:
        tok = request.args.get("token") or ""
    return hmac.compare_digest(tok.encode(), ADMIN_TOKEN.encode())


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
  <div class="card"><b>{{pv}}</b><span>累计访问（同一访客 60 秒内只计一次）</span></div>
  <div class="card"><b>{{uv24}}</b><span>近 24h 独立访客</span></div>
  <div class="card"><b>{{uv_all}}</b><span>累计独立访客</span></div>
</div>
<table><thead><tr>
  <th>#</th><th>IP（已脱敏）</th><th>地区</th><th>设备</th><th>系统</th><th>浏览器</th><th>来源</th><th>路径</th><th>时间(北京)</th>
</tr></thead><tbody>
{% for r in rows %}
<tr><td>{{loop.index}}</td><td>{{r[0]}}</td>
<td>{{r[1]}}{% if r[2] %}·{{r[2]}}{% endif %}{% if r[3] %}·{{r[3]}}{% endif %}</td>
<td><span class="tag">{{r[4]}}</span></td><td>{{r[5]}}</td><td>{{r[6]}}</td>
<td>{{r[8][:40]}}</td><td>{{r[7]}}</td><td>{{r[9]}}</td></tr>
{% endfor %}
</tbody></table>
</body></html>"""


def to_local(ts):
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
        return t.astimezone(DISPLAY_TZ).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return ts


@app.route("/admin")
def admin():
    if not admin_ok():
        abort(401)
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT ip,country,region,city,device,os,browser,path,referer,ts FROM visits ORDER BY id DESC LIMIT 200")
    rows = [list(r) for r in c.fetchall()]
    pv, uv24, uv_all = _counters(conn)
    conn.close()
    for r in rows:
        r[4] = DEVICE_CN.get(r[4], r[4])
        r[9] = to_local(r[9])
    return render_template_string(ADMIN_HTML, rows=rows, pv=pv, uv24=uv24, uv_all=uv_all)


@app.route("/")
def index():
    return jsonify({"service": "moto-dashboard stats", "endpoints": ["/api/visit", "/api/stats", "/admin"]})


init_db()   # 模块级初始化：用 gunicorn / flask run 启动也不会缺表


if __name__ == "__main__":
    if not ALLOW_ORIGIN:
        print("[warn] 未设置 ALLOW_ORIGIN，前端跨域上报会被浏览器拦截")
    if GEO_ENABLE:
        print("[warn] 归属地走 ip-api.com（http 明文、第三方），不希望外发可设 GEO_ENABLE=0")
    print("stats_server listening on :%d（开发服务器，仅供本地调试；生产请用 gunicorn，见文件头）" % PORT)
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=PORT, debug=False)
