#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
「中国市场 250cc 以上摩托车品牌看板」官方 Logo 本地化采集脚本。

阶段1 phase1 : 下载 brands_*.json 中已有 logoUrl 的品牌（含相对路径补全）。
阶段2 phase2 : 对 logoUrl 为空或下载失败的品牌，抓官网首页 HTML 解析
               <img>/CSS background-image/<link rel=icon>/og:image，
               并有限尝试 m.58moto.com 品牌页兜底。
复核   strict : 剔除人工目视确认非 Logo 的图片(宣传图/车型海报/UI图标/箭头/
               热线横幅/品牌错配)，并对相关品牌只按含 logo/icon 的候选定向补抓。
报告   report : 复核 assets/logos/ 文件头，打印成功/失败统计。

用法: python assets/fetch_logos.py phase1|phase2|strict|report
状态累积写入 data/logos.json，可重复运行、不会重复下载已成功品牌。
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.parse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
LOGOS_DIR = os.path.join(ROOT, 'assets', 'logos')
TMP_DIR = os.path.join(ROOT, 'assets', '_probe')
TMP = os.path.join(TMP_DIR, 'dl.tmp')
STATE = os.path.join(DATA, 'logos.json')

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
TIMEOUT = 15
MAX_CANDIDATES = 10          # 每个品牌最多尝试的候选 URL 数
EXTS = ('png', 'jpg', 'svg', 'webp', 'gif')

os.makedirs(LOGOS_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)


# ---------------------------------------------------------------- 基础 IO

def load_brands():
    brands = []
    for f in sorted(glob.glob(os.path.join(DATA, 'brands_*.json'))):
        with open(f, encoding='utf-8') as fh:
            d = json.load(fh)
        for b in d.get('brands', []):
            brands.append(b)
    return brands


def load_state():
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def save_state(state, brands):
    """保证每个品牌恰好一条记录，顺序与 brands_*.json 一致。"""
    ordered = {}
    for b in brands:
        bid = b['id']
        ordered[bid] = state.get(bid, {
            'file': None, 'source': None, 'status': 'missing',
            'reason': '未执行抓取',
        })
    with open(STATE, 'w', encoding='utf-8') as fh:
        json.dump(ordered, fh, ensure_ascii=False, indent=2)
    return ordered


def domain_root(u):
    try:
        p = urllib.parse.urlparse(u)
        if p.netloc:
            return '%s://%s/' % (p.scheme or 'https', p.netloc)
    except Exception:
        pass
    return None


def abs_url(u, base):
    if not u:
        return None
    u = u.strip().replace('&amp;', '&')
    if u.startswith(('data:', 'javascript:', '#')):
        return None
    if u.startswith('//'):
        return 'https:' + u
    if u.startswith(('http://', 'https://')):
        return u
    return urllib.parse.urljoin(base, u) if base else None


def read_tmp():
    if os.path.exists(TMP):
        return open(TMP, 'rb').read()
    return b''


def clear_tmp():
    if os.path.exists(TMP):
        os.remove(TMP)


# ---------------------------------------------------------------- 下载与校验

def curl(url, dest, referer=None):
    cmd = ['curl', '-sL', '-A', UA,
           '--max-time', str(TIMEOUT), '--connect-timeout', '8',
           '-o', dest, '-w', '%{http_code}|%{content_type}']
    if referer:
        cmd += ['-e', referer]
    cmd += [url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=TIMEOUT + 8)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return 'timeout|-'
    except Exception:
        return 'error|-'


def sniff(data):
    """按文件头判定真实图片；HTML / 空白 / 404 页面一律判失败。"""
    if not data or len(data) < 8:
        return None
    low = data[:8192].lower()
    if b'<html' in low or b'<!doctype html' in low or b'<head' in low:
        return None
    if data.startswith(b'\x89PNG'):
        return 'png'
    if data.startswith(b'\xff\xd8'):
        return 'jpg'
    if data[:4] == b'RIFF' and b'WEBP' in data[:16]:
        return 'webp'
    if data.startswith(b'GIF8'):
        return 'gif'
    if b'<svg' in low:
        return 'svg'
    return None


def save_logo(bid, data, ext, source):
    dest = os.path.join(LOGOS_DIR, bid + '.' + ext)
    with open(dest, 'wb') as fh:
        fh.write(data)
    for e in EXTS:
        p = os.path.join(LOGOS_DIR, bid + '.' + e)
        if p != dest and os.path.exists(p):
            os.remove(p)
    return {
        'file': 'assets/logos/%s.%s' % (bid, ext),
        'source': source,
        'status': 'ok',
    }


def try_candidates(bid, urls, homepage=None):
    """逐个尝试候选 URL；成功即返回记录，全部失败返回 None。"""
    attempted = 0
    for u in urls:
        if not u or attempted >= MAX_CANDIDATES:
            break
        attempted += 1
        root = domain_root(homepage or u)
        info = curl(u, TMP, 'https://www.google.com/')
        code = info.split('|')[0] if '|' in info else info
        data = read_tmp()
        ext = sniff(data)
        # 仅在疑似防盗链(403/401)时，用官网域名 Referer 再试一次
        if not ext and code in ('403', '401') and root:
            info = curl(u, TMP, root)
            data = read_tmp()
            ext = sniff(data)
        if ext:
            clear_tmp()
            return save_logo(bid, data, ext, u)
        clear_tmp()
    return None


def fetch_html(url):
    info = curl(url, TMP, 'https://www.google.com/')
    data = read_tmp()
    clear_tmp()
    code = info.split('|')[0] if '|' in info else info
    if len(data) < 200 or not code.startswith('2'):
        return None
    return data.decode('utf-8', errors='ignore')


# ---------------------------------------------------------------- HTML 解析

def parse_candidates(html, base):
    """从官网 HTML 提取 Logo 候选 URL，按可信度降序去重。"""
    scored = []

    def add(score, u):
        a = abs_url(u, base)
        if not a:
            return
        if (re.search(r'logo|brand', a, re.I)
                or re.search(r'\.(png|jpe?g|svg|webp|gif|ico)(\?|#|$)', a, re.I)):
            scored.append((score, a))

    # <img> / 懒加载属性
    for m in re.finditer(r'<img\b[^>]*>', html, re.I):
        tag = m.group(0)
        sm = re.search(
            r'\b(?:src|data-src|data-original|data-lazy-src)\s*=\s*["\']([^"\']+)["\']',
            tag, re.I)
        if sm:
            add(4 if re.search(r'logo|brand', tag, re.I) else 2, sm.group(1))

    # CSS background-image: url(...)
    for m in re.finditer(r'url\(\s*["\']?([^)"\']+)["\']?\s*\)', html, re.I):
        u = m.group(1)
        add(3 if re.search(r'logo|brand', u, re.I) else 1, u)

    # <link rel="icon"> / apple-touch-icon
    for m in re.finditer(r'<link\b[^>]*>', html, re.I):
        tag = m.group(0)
        if re.search(r'rel\s*=\s*["\'][^"\']*icon', tag, re.I):
            hm = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if hm:
                add(2, hm.group(1))

    # og:image / twitter:image
    for m in re.finditer(r'<meta\b[^>]*>', html, re.I):
        tag = m.group(0)
        if re.search(r'og:image|twitter:image|itemprop=["\']image', tag, re.I):
            cm = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if cm:
                add(1, cm.group(1))

    seen, out = set(), []
    for score, u in sorted(scored, key=lambda x: -x[0]):
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def is_challenge(html):
    """58moto 等站点返回 JS 反爬挑战页，无有效图片直链。"""
    return ('function M()' in html or 'var GH=[' in html
            or 'document.cookie' in html and '<img' not in html)


def moto58_id(b):
    s = json.dumps(b, ensure_ascii=False)
    ids = re.findall(r'58moto\.com/brand/(\d+)', s)
    return ids[0] if ids else None


# ---------------------------------------------------------------- 阶段实现

def phase1(brands, state):
    todo = [b for b in brands
            if b.get('logoUrl') and state.get(b['id'], {}).get('status') != 'ok']
    print('[phase1] 待处理 %d 个带 logoUrl 的品牌' % len(todo))
    ok = 0
    for i, b in enumerate(todo, 1):
        bid = b['id']
        u = abs_url(b['logoUrl'], b.get('website'))
        print('  (%d/%d) %-20s %s' % (i, len(todo), bid, (u or '')[:95]),
              end=' ... ', flush=True)
        res = try_candidates(bid, [u], b.get('website'))
        if res:
            state[bid] = res
            ok += 1
            size = os.path.getsize(os.path.join(ROOT, res['file']))
            print('OK  %s (%d bytes)' % (res['file'], size))
        else:
            state[bid] = {
                'file': None, 'source': None, 'status': 'missing',
                'reason': 'logoUrl 直链下载失败或返回非图片内容(HTML/404/空白)',
            }
            print('FAIL')
    save_state(state, brands)
    print('[phase1] 完成: 成功 %d / %d' % (ok, len(todo)))


def phase2(brands, state):
    todo = [b for b in brands
            if state.get(b['id'], {}).get('status') != 'ok']
    print('[phase2] 待补抓 %d 个品牌' % len(todo))
    ok = 0
    for i, b in enumerate(todo, 1):
        bid = b['id']
        web = b.get('website')
        cands, notes = [], []
        print('  (%d/%d) %-20s' % (i, len(todo), bid), end=' ... ', flush=True)

        if web:
            html = fetch_html(web)
            if html is None:
                notes.append('官网首页无法访问')
            elif is_challenge(html):
                notes.append('官网返回JS反爬挑战页')
            else:
                got = parse_candidates(html, web)
                if got:
                    cands += got
                else:
                    notes.append('官网HTML未解析到图片直链(疑似SPA/纯JS渲染)')
        else:
            notes.append('品牌数据无官网地址，也无官方Logo直链')

        # 58moto 有限兜底（PC/移动版多为反爬挑战页）
        mid = moto58_id(b)
        if mid:
            h2 = fetch_html('https://m.58moto.com/brand/%s' % mid)
            if h2 and not is_challenge(h2):
                cands += parse_candidates(h2, 'https://m.58moto.com/')
            else:
                notes.append('58moto品牌页为反爬挑战页')

        # 阶段1 失败者：把原 logoUrl 放到候选末尾再给一次机会
        if b.get('logoUrl'):
            u = abs_url(b['logoUrl'], web)
            if u and u not in cands:
                cands.append(u)

        res = try_candidates(bid, cands, web) if cands else None
        if res:
            state[bid] = res
            ok += 1
            size = os.path.getsize(os.path.join(ROOT, res['file']))
            print('OK  %s (%d bytes)  <- %s' % (res['file'], size, res['source'][:70]))
        else:
            state[bid] = {
                'file': None, 'source': None, 'status': 'missing',
                'reason': '；'.join(notes) if notes else '所有候选URL均非真实图片',
            }
            print('MISS (%s)' % state[bid]['reason'][:80])
    save_state(state, brands)
    print('[phase2] 完成: 成功 %d / %d' % (ok, len(todo)))


# ---------------------------------------------------------------- 严格复核/补抓

# 人工目视 + 来源复核结论：下列文件虽通过文件头校验，但并非品牌 Logo，
# 按「只使用真实品牌官方 Logo」的硬性要求判失败并删除。
KNOWN_BAD = {
    'souo': '官网解析仅得到实验室整车照片(brand.jpg)，非品牌Logo',
    'suzuki': '官网解析仅得到船外机新品宣传横幅(kv32.jpg)，非品牌Logo',
    'wuyang-honda': '官网解析仅得到NW T150车型海报(CMS配图)，非品牌Logo',
    'sundiro-honda': '官网解析仅得到18x18关闭按钮图标(closeIconWhite.png)，非品牌Logo',
    'ducati': '官网解析仅得到12x6下拉箭头SVG(down.svg)，非品牌Logo',
    'mv-agusta': '官网解析仅得到官网网址+服务热线横幅(dfdf2.gif)，非品牌Logo',
    'loncin': '预置logoUrl指向第三方演示站qiniu.mfdemo.cn，图中字样为VOGE(无极)而非LONCIN，非隆鑫官方Logo',
}

# 定向补抓时额外尝试的官网首页
STRICT_PAGES = {
    'souo': ['https://www.souomoto.com/'],
    'wuyang-honda': ['https://www.wuyang-honda.com/'],
    'sundiro-honda': ['https://www.honda-sundiro.com/'],
    'ducati': ['https://www.ducatichina.cn/'],
    'suzuki': ['http://www.suzuki-china.com/'],
    'mv-agusta': ['http://www.chinamvagusta.com/'],
    'loncin': ['https://www.loncinindustries.com/'],
    'voge': ['https://vogemotor.com/', 'https://www.vogemotor.com/home/'],
}


def strict_filter(html, base):
    """只保留 URL 明确含 logo / icon 的候选，排除内容图与 UI 图标。"""
    out = []
    for u in parse_candidates(html, base):
        low = u.lower()
        if not re.search(r'logo|apple-touch-icon|favicon|brand-mark', low):
            continue
        if re.search(r'closeicon|/down\.|kv\d|banner|/news/|/archive/|hotline|btn|arrow|icon-white', low):
            continue
        out.append(u)
    return out


def phase_strict(brands, state):
    targets = list(dict.fromkeys(list(KNOWN_BAD) + list(STRICT_PAGES)))
    print('[strict] 严格复核 %d 个品牌（剔除伪Logo + 只认含logo/icon的候选）' % len(targets))

    # 1) 删除已确认非 Logo 的文件，置 missing
    for bid, reason in KNOWN_BAD.items():
        for e in EXTS:
            p = os.path.join(LOGOS_DIR, bid + '.' + e)
            if os.path.exists(p):
                os.remove(p)
        state[bid] = {'file': None, 'source': None, 'status': 'missing',
                      'reason': reason}
        print('  剔除 %-18s %s' % (bid, reason[:58]))

    # 2) 定向补抓（每个品牌最多 3 个页面、10 个候选）
    ok = 0
    for bid in targets:
        if state.get(bid, {}).get('status') == 'ok':
            continue
        primary = next((b.get('website') for b in brands if b['id'] == bid), None)
        pages = STRICT_PAGES.get(bid, [])
        if primary and primary not in pages:
            pages = [primary] + pages
        cands = []
        for pg in pages[:3]:
            h = fetch_html(pg)
            if h and not is_challenge(h):
                cands += strict_filter(h, pg)
        seen, uniq = set(), []
        for u in cands:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        print('  补抓 %-18s 候选 %2d 个' % (bid, len(uniq)), end=' ... ', flush=True)
        res = try_candidates(bid, uniq, primary) if uniq else None
        if res:
            state[bid] = res
            ok += 1
            print('OK  %s <- %s' % (res['file'], res['source'][:75]))
        else:
            print('MISS')
    save_state(state, brands)
    print('[strict] 完成: 补抓成功 %d' % ok)


def report(brands, state):
    print('[report] 复核文件头与状态 ...')
    state = save_state(state, brands)
    ok_ids, miss_ids = [], []
    for b in brands:
        bid = b['id']
        rec = state.get(bid, {})
        if rec.get('status') == 'ok' and rec.get('file'):
            p = os.path.join(ROOT, rec['file'])
            if not os.path.exists(p):
                state[bid] = {'file': None, 'source': None, 'status': 'missing',
                              'reason': '记录为ok但文件已丢失'}
                miss_ids.append(bid)
                continue
            data = open(p, 'rb').read()
            if not sniff(data):
                os.remove(p)
                state[bid] = {'file': None, 'source': None, 'status': 'missing',
                              'reason': '文件头校验失败(非真实图片)，已删除'}
                miss_ids.append(bid)
                continue
            ok_ids.append(bid)
        else:
            miss_ids.append(bid)
    save_state(state, brands)
    print('\n=== 统计 ===')
    print('品牌总数: %d   成功: %d   失败: %d' %
          (len(brands), len(ok_ids), len(miss_ids)))
    print('\n成功清单:')
    for bid in ok_ids:
        print('  %-20s %s' % (bid, state[bid]['file']))
    print('\n失败清单:')
    name_of = {b['id']: b.get('name') for b in brands}
    for bid in miss_ids:
        print('  %-20s %-12s %s' %
              (bid, name_of.get(bid), state[bid].get('reason', '')))
    print('\n文件目录: %s' % LOGOS_DIR)
    print('映射文件: %s' % STATE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['phase1', 'phase2', 'strict', 'report'])
    args = ap.parse_args()
    brands = load_brands()
    state = load_state()
    print('品牌清单: %d 个' % len(brands))
    if args.phase == 'phase1':
        phase1(brands, state)
    elif args.phase == 'phase2':
        phase2(brands, state)
    elif args.phase == 'strict':
        phase_strict(brands, state)
    else:
        report(brands, state)


if __name__ == '__main__':
    main()
