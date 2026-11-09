#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本轮 8 品牌官方 Logo 补抓 / 校验工具。
用法: python assets/round2.py run1|run2
run1: 8 个中国官网首页 + 常见 favicon/logo 直链猜测
run2: 全球官网 / 移动端 / 备用页面（供未成功品牌二次尝试）
结果: assets/_probe/round2/ok/ 下为通过【文件头+Pillow】基础校验的候选，
      并写 manifest.json 记录 URL/尺寸/主色，供人工 ViewImage 目视复核。
"""
import os, re, sys, json, subprocess, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, 'assets', '_probe', 'round2')
DL = os.path.join(PROBE, 'dl')
OK = os.path.join(PROBE, 'ok')
for d in (PROBE, DL, OK):
    os.makedirs(d, exist_ok=True)

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
TIMEOUT = 15

PRIMARY = {
    'yamaha':        ['https://www.yamaha-motor.com.cn/', 'https://www.yamaha-motor.com.cn/mc/products'],
    'suzuki':        ['http://www.suzuki-china.com/'],
    'ducati':        ['https://www.ducatichina.cn/'],
    'zontes':        ['https://www.zontes.com/ch/'],
    'jianshe-yamaha':['https://www.jym.com.cn/'],
    'sundiro-honda': ['https://www.honda-sundiro.com/'],
    'qingqi-suzuki': ['https://www.qssuzuki.com.cn/'],
    'mv-agusta':     ['http://www.chinamvagusta.com/'],
}

# 第二轮只针对 run1 未拿到可用 Logo 的品牌，避免重复请求与覆盖已确认文件
FALLBACK = {
    'yamaha':        ['https://global.yamaha-motor.com/', 'https://www.yamaha-motor.com.cn/mc/'],
    'zontes':        ['https://www.zontes.com/', 'https://www.zontes.com/en/', 'http://www.zontes.com/ch/'],
    'jianshe-yamaha':['https://www.jym.com.cn/product/', 'http://www.jym.com.cn/'],
    'qingqi-suzuki': ['http://www.qssuzuki.com.cn/', 'https://www.qssuzuki.com.cn/index.html'],
    'mv-agusta':     ['https://www.mvagusta.com/', 'http://www.chinamvagusta.com/products_2.asp?tid=1551&id=1231'],
}

GUESS = ['/favicon.ico', '/apple-touch-icon.png', '/logo.png', '/logo.svg',
         '/images/logo.png', '/img/logo.png', '/static/images/logo.png',
         '/assets/images/logo.png']


def origin(u):
    p = urllib.parse.urlparse(u)
    if p.netloc:
        return '%s://%s' % (p.scheme or 'https', p.netloc)
    return None


def curl(url, dest, referer=None):
    cmd = ['curl', '-sL', '-A', UA, '--max-time', str(TIMEOUT),
           '--connect-timeout', '8', '-o', dest,
           '-w', '%{http_code}|%{content_type}']
    if referer:
        cmd += ['-e', referer]
    cmd += [url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT + 8)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return 'timeout|-'
    except Exception:
        return 'error|-'


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


def sniff(data):
    if not data or len(data) < 4:
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
    if data[:4] == b'\x00\x00\x01\x00':
        return 'ico'
    if b'<svg' in low:
        return 'svg'
    return None


def parse_page(html, base):
    """返回 (候选URL列表, 备注)。只保留疑似 logo/icon/favicon 与 og:image。"""
    scored = []

    def add(score, u):
        a = abs_url(u, base)
        if not a:
            return
        scored.append((score, a))

    for m in re.finditer(r'<img\b[^>]*>', html, re.I):
        tag = m.group(0)
        sm = re.search(r'\b(?:src|data-src|data-original|data-lazy-src)\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if sm:
            add(5 if re.search(r'logo|brand', tag, re.I) else 0, sm.group(1))
    for m in re.finditer(r'url\(\s*["\']?([^)"\']+)["\']?\s*\)', html, re.I):
        u = m.group(1)
        add(4 if re.search(r'logo|brand', u, re.I) else 0, u)
    for m in re.finditer(r'<link\b[^>]*>', html, re.I):
        tag = m.group(0)
        if re.search(r'rel\s*=\s*["\'][^"\']*icon', tag, re.I):
            hm = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if hm:
                add(6, hm.group(1))
    for m in re.finditer(r'<meta\b[^>]*>', html, re.I):
        tag = m.group(0)
        if re.search(r'og:image|twitter:image|itemprop=["\']image', tag, re.I):
            cm = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if cm:
                add(1, cm.group(1))

    out, seen = [], set()
    for score, u in sorted(scored, key=lambda x: -x[0]):
        low = u.lower()
        if score == 0:                       # 普通 img/背景：仅当 URL 含 logo/icon 才留
            if not re.search(r'logo|icon|favicon|brand', low):
                continue
        # 明显的内容图/横幅/车型图/UI 图标排除
        if re.search(r'kv\d|banner|/news/|/product/|/upload/|hotline|closeicon|/down\.|arrow|btn|loading|placeholder', low) \
                and not re.search(r'logo|apple-touch-icon|favicon|brand-mark', low):
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def is_challenge(html):
    return (len(html) < 200 or 'function M()' in html or 'var GH=[' in html
            or ('document.cookie' in html and '<img' not in html))


# ---------------------------------------------------------------- 页面抓取
def fetch_page(task):
    bid, url = task
    key = re.sub(r'[^a-zA-Z0-9]+', '_', bid + '_' + url)[-70:]
    dest = os.path.join(DL, 'page__' + key + '.html')
    info = curl(url, dest)
    data = open(dest, 'rb').read() if os.path.exists(dest) else b''
    code = info.split('|')[0] if '|' in info else info
    return bid, url, code, data


def collect(bid, pages, html_infos):
    """聚合某品牌所有页面的候选 + 各 origin 的猜测直链。"""
    cands, notes = [], []
    for (purl, code, data) in html_infos:
        if not data or len(data) < 200 or not code.startswith('2'):
            notes.append('%s -> %s' % (urllib.parse.urlparse(purl).netloc, code))
            continue
        html = data.decode('utf-8', errors='ignore')
        if is_challenge(html):
            notes.append('%s -> JS挑战页' % urllib.parse.urlparse(purl).netloc)
            continue
        got = parse_page(html, purl)
        cands += got
        notes.append('%s -> %dB, 候选%d' % (urllib.parse.urlparse(purl).netloc, len(data), len(got)))
    # 猜测直链（基于所有页面 origin）
    origins = []
    for p in pages:
        o = origin(p)
        if o and o not in origins:
            origins.append(o)
    for o in origins:
        for g in GUESS:
            cands.append(o + g)
    # 去重保序、限量
    seen, uniq = set(), []
    for u in cands:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq[:16], notes


# ---------------------------------------------------------------- 图片下载 + 校验
def color_info(path, ext):
    from PIL import Image
    info = {}
    im = Image.open(path)
    w, h = im.size
    info['w'], info['h'] = w, h
    im = im.convert('RGBA')
    im.thumbnail((80, 80))
    px = list(im.getdata())
    opaque = [p for p in px if p[3] > 40]
    info['transparent'] = round(1 - len(opaque) / len(px), 3) if px else 1
    if not opaque:
        info['pred'] = None
        return info
    q = Counter((r // 24 * 24, g // 24 * 24, b // 24 * 24) for r, g, b, a in opaque)
    pred, cnt = q.most_common(1)[0]
    info['pred'] = '#%02X%02X%02X' % pred
    info['pred_ratio'] = round(cnt / len(opaque), 3)
    lums = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b, a in opaque]
    mean = sum(lums) / len(lums)
    std = (sum((l - mean) ** 2 for l in lums) / len(lums)) ** 0.5
    info['mean_lum'] = round(mean, 1)
    info['std_lum'] = round(std, 1)
    nw = sum(1 for r, g, b, a in opaque if not (r > 235 and g > 235 and b > 235))
    info['nonwhite'] = round(nw / len(opaque), 3)
    return info


def svg_info(data):
    txt = data.decode('utf-8', errors='ignore')
    head = txt[:2000]
    wm = re.search(r'\bwidth\s*=\s*["\']?([\d.]+)', head, re.I)
    hm = re.search(r'\bheight\s*=\s*["\']?([\d.]+)', head, re.I)
    vb = re.search(r'viewBox\s*=\s*["\']\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)', head, re.I)
    w = float(wm.group(1)) if wm else (float(vb.group(3)) if vb else 0)
    h = float(hm.group(1)) if hm else (float(vb.group(4)) if vb else 0)
    shapes = len(re.findall(r'<(path|circle|rect|polygon|polyline|ellipse|text|g|use)\b', txt, re.I))
    fills = re.findall(r'fill\s*=\s*["\']([^"\']+)["\']', txt, re.I)
    return {'w': w, 'h': h, 'shapes': shapes,
            'pred': (Counter(fills).most_common(1)[0][0] if fills else None)}


def analyze(path, ext, data):
    """返回 (是否通过, 原因, info)。"""
    if ext == 'svg':
        info = svg_info(data)
        if info['w'] < 30 or info['h'] < 12:
            return False, 'SVG尺寸过小(%sx%s)' % (info['w'], info['h']), info
        if info['shapes'] < 1:
            return False, 'SVG无任何图形元素', info
        return True, 'SVG ok', info
    try:
        info = color_info(path, ext)
    except Exception as e:
        return False, 'Pillow打开失败: %s' % e, {}
    w, h = info.get('w', 0), info.get('h', 0)
    if w < 30 or h < 12:
        return False, '尺寸过小(%dx%d)' % (w, h), info
    if info.get('std_lum', 0) < 10 and info.get('mean_lum', 0) > 200:
        return False, '几乎纯白/纯灰无图形对比', info
    if info.get('nonwhite', 0) < 0.01:
        return False, '几乎纯白无图形', info
    white = (info.get('transparent', 0) > 0.3 and info.get('mean_lum', 0) > 170
             and info.get('std_lum', 0) > 15)
    info['white_mark'] = bool(white)
    return True, '疑似白色字标需深色底' if white else 'ok', info


def save_and_analyze(task):
    """下载落盘 -> 校验 -> 通过则写入 OK 目录。"""
    bid, idx, url = task
    dest = os.path.join(DL, '%s__%02d.bin' % (bid, idx))
    info = curl(url, dest, 'https://www.google.com/')
    code = info.split('|')[0] if '|' in info else info
    data = open(dest, 'rb').read() if os.path.exists(dest) else b''
    ext = sniff(data)
    if not ext and code in ('403', '401'):
        curl(url, dest, origin(url))
        data = open(dest, 'rb').read() if os.path.exists(dest) else b''
        ext = sniff(data)
    if not ext:
        return {'bid': bid, 'idx': idx, 'url': url, 'code': code,
                'ext': None, 'ok': False, 'reason': '非图片(HTML/404/空白) code=%s' % code}
    ok, reason, cinfo = analyze(dest, ext, data)
    rec = {'bid': bid, 'idx': idx, 'url': url, 'code': code, 'ext': ext,
           'ok': bool(ok), 'reason': reason, 'info': cinfo}
    if ok:
        keep = os.path.join(OK, '%s__%02d.%s' % (bid, idx, ext))
        with open(keep, 'wb') as fh:
            fh.write(data)
        rec['keep'] = keep
    return rec


def run(which):
    pages_map = PRIMARY if which == 'run1' else FALLBACK
    # 1) 并发抓页面
    page_tasks = [(bid, u) for bid, pages in pages_map.items() for u in pages]
    page_results = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(fetch_page, t) for t in page_tasks]
        for f in as_completed(futs):
            bid, url, code, data = f.result()
            page_results.setdefault(bid, []).append((url, code, data))
    # 2) 聚合候选
    cand_tasks = []
    print('==== 页面探测 ====')
    for bid, pages in pages_map.items():
        uniq, notes = collect(bid, pages, page_results.get(bid, []))
        print('  %-16s %s' % (bid, ' | '.join(notes)))
        print('    候选 %d: %s' % (len(uniq), '  '.join(u[:60] for u in uniq[:6])))
        for i, u in enumerate(uniq):
            cand_tasks.append((bid, i, u))
    # 3) 并发下载 + 校验
    print('\n==== 候选下载/校验 (%d 个) ====' % len(cand_tasks))
    results = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(save_and_analyze, t) for t in cand_tasks]
        for f in as_completed(futs):
            results.append(f.result())
    results.sort(key=lambda r: (r['bid'], r['idx']))
    # 4) 报告
    print('\n==== 通过基础校验的候选 ====')
    manifest = {}
    for r in results:
        if not r['ok']:
            continue
        i = r['info']
        print('  [%s] %s  %dx%d  pred=%s 透明=%.2f 亮度=%.0f/%.0f  %s  <- %s' % (
            r['bid'], r['ext'], i.get('w', 0), i.get('h', 0),
            i.get('pred'), i.get('transparent', 0), i.get('mean_lum', 0),
            i.get('std_lum', 0), r['reason'], r['url'][:85]))
        manifest.setdefault(r['bid'], []).append(
            {'file': r.get('keep'), 'url': r['url'], 'ext': r['ext'],
             'info': i, 'reason': r['reason']})
    with open(os.path.join(PROBE, 'manifest_%s.json' % which), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print('\nmanifest 已写: %s' % os.path.join(PROBE, 'manifest_%s.json' % which))
    print('OK 目录: %s' % OK)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'run1')
