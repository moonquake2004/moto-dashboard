#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性数据修正：处理 2026-11-22 核实的 15 条排量冲突。

用法（在仓库根目录）：
    python scripts/fix_cc_conflicts_20261122.py          # 预览（dry-run），不写文件
    python scripts/fix_cc_conflicts_20261122.py --apply  # 写回 data/brands_*.json 与 data/specs.js
之后：python build_data.py --check && python build_data.py

脚本是幂等的：重复执行不会重复修改；找不到目标记录时只告警不报错。
被删除的 specs 条目备份到 data/_removed_specs_20261122.json，便于重抓后对照。
"""
# ---- 已归档：此脚本已执行过，数据已落库。重跑可能覆盖之后的人工修改。----
# 原用途：2026-11-22 排量冲突修正
import os as _os, sys as _sys
if _os.environ.get("RUN_ARCHIVED") != "1":
    _sys.exit("已归档的一次性脚本，默认不执行；确需重跑请设 RUN_ARCHIVED=1")
# ---------------------------------------------------------------------
import argparse, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
QJ = "https://www.qjmotor.com/car.html?id=%d"
TODAY = "2026-11-22"

# ---- 1. 型号表字段修正：(品牌 id, 型号名) -> 要覆盖的字段 ----
PATCH = {
    ("qjmotor", "赛600"):  {"cc": 680, "price": "34999元", "source": QJ % 153},   # 官网 2027款赛600：680cc / ¥34,999
    ("qjmotor", "骁600"):  {"cc": 554, "source": QJ % 79},                         # 官网：554cc，公路版 ¥29,999
    ("qjmotor", "追600"):  {"source": QJ % 41},                                     # 600cc 正确，只补官网来源
    ("voge", "DS625X"):    {"cc": 581},   # 76×64 双缸 = 580.7cc
    ("voge", "CU530"):     {"cc": 500},
    ("sym", "HUSKY ADV 300 哈士奇（含26款旗舰款/弯道版）"): {"cc": 278},          # 三阳官网 278ml
    # 长江750：保持 650。复活版实际搭载春风 650cc 并列双缸（见 fix_re_changjiang.py 的存疑说明），
    # 参数表里的 749cc 是「经典复刻」老款水平对置版本，属于抓错 → 删参数，不改型号表
    ("cyclone", "RA600"):  {"cc": 560},   # 三款同一台双缸（与参数表一致）
    ("cyclone", "AQS600"): {"cc": 560},
    ("cyclone", "RX600"):  {"cc": 560},
    # ---- 钱江全系官网核对（qjmotor.com 车型详情页「主要技术参数」，2026-11-22）----
    ("qjmotor", "赛250"):   {"cc": 249, "source": QJ % 57},
    ("qjmotor", "赛421"):   {"source": QJ % 107},
    ("qjmotor", "赛450"):   {"cc": 449, "price": "23999元", "source": QJ % 50},        # 官网 ¥23,999（库里 26999）
    ("qjmotor", "赛550"):   {"cc": 554, "source": QJ % 128},                          # 官网名 赛550ES
    ("qjmotor", "赛800"):   {"cc": 778, "price": "42999~49999元", "source": QJ % 112}, # 800RS ¥42,999 / 800RC ¥49,999
    ("qjmotor", "赛921"):   {"source": QJ % 75},
    ("qjmotor", "Super921"): {"source": QJ % 109},
    ("qjmotor", "闪250"):   {"cc": 249, "source": QJ % 93},
    ("qjmotor", "闪300"):   {"cc": 296, "source": QJ % 46},                           # 闪300 296cc；AMT 版 300cc
    ("qjmotor", "闪350"):   {"cc": 343, "price": "24999元", "source": QJ % 47},
    ("qjmotor", "闪400"):   {"source": QJ % 148},
    ("qjmotor", "骁650"):   {"cc": 645, "price": "46999元起", "source": QJ % 29},
    ("qjmotor", "骁700S"):  {"cc": 698, "price": "37999元起", "source": QJ % 90},
    ("qjmotor", "骁800"):   {"cc": 799, "price": "49999元起", "source": QJ % 31},
    ("qjmotor", "追550"):   {"cc": 549, "source": QJ % 77},
    ("qjmotor", "追800"):   {"cc": 778, "price": "47999元", "source": QJ % 113},
    ("qjmotor", "追900"):   {"cc": 904, "source": QJ % 114},
    ("qjmotor", "追921"):   {"source": QJ % 126},
    ("qjmotor", "逸550"):   {"cc": 549, "price": "33999元", "source": QJ % 43},
    ("qjmotor", "鸿250"):   {"cc": 249, "source": QJ % 98},
    ("qjmotor", "鸿350GS"): {"cc": 330, "source": QJ % 122},
}

# ---- 2. 闪600 拆成三条（官网四款排量 550–600cc，合并一条无法对齐参数） ----
SPLIT = {
    ("qjmotor", "闪600"): [
        {"name": "闪600",            "cc": 600, "type": "巡航", "price": "35999元",        "source": QJ % 63},
        {"name": "闪600 V2 Classic", "cc": 550, "type": "巡航", "price": "24999元",        "source": QJ % 125},
        {"name": "闪600 V4",         "cc": 560, "type": "巡航", "price": "31999~32999元",  "source": QJ % 129},
    ],
}
# 参数表键随拆分改名：原「闪600」参数实为 V4 版本
SPEC_RENAME = {"钱江|闪600": "钱江|闪600 V4"}

# ---- 3. 移入「存疑」：不计入统计，等待人工确认 ----
TO_UNCERTAIN = {
    ("lifan", "K19"): "力帆官网仅有 LF150-14P（K19 青春版，150cc）；250cc 车型为 K29（LF250-14M）。待确认原记录应为 K29 还是应删除。",
    ("qjmotor", "SRT450"): "QJMOTOR 官网 50 款摩托车列表（%s）无 SRT450；且该型号已同时记在 uncertain 里，正式清单与存疑重复。" % TODAY,
    ("cyclone", "RT450"): "赛科龙官网产品菜单（%s）未列 RT450，仅有 RT250/RT150S/RT150E；在售状态待确认。" % TODAY,
    ("xiangshuai", "欧若拉400T"): "摩托范参数页标 350cc 单缸，与型号名 400 不符；无官网可核，待人工确认排量。",
}

# ---- 4. 删除参数（抓错版本，需按正确车型重抓） ----
SPEC_REMOVE = {
    "钱江|追600": "参数实为追600RS（680cc/74.5kW/201kg），需按追600（600cc/60kW/229kg）重抓",
    "力帆|K19": "参数为 150cc 青春版",
    "赛科龙|RT450": "车型移入存疑",
    "香帅机车|欧若拉400T": "车型移入存疑",
    "钱江|鸿350GS": "参数排量 350cc，官网实为 330cc，需重抓",
    "钱江|SRT450": "车型移入存疑",
    "长江摩托|长江750 CJ750": "参数为经典复刻水平对置 749cc 版本；收录车型为春风 650cc 并列双缸版，需重抓",
}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, obj):
    raw = open(p, "rb").read(4096)
    nl = "\r\n" if b"\r\n" in raw else "\n"
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    with open(p + ".tmp", "wb") as f:
        f.write(text.replace("\n", nl).encode("utf-8"))
    os.replace(p + ".tmp", p)


def fix_brands(apply):
    hit, log = set(), []
    for path in sorted(glob.glob(os.path.join(DATA, "brands_*.json"))):
        doc, changed = load(path), False
        for b in doc["brands"]:
            bid, new_models = b.get("id"), []
            for m in b.get("models", []):
                key = (bid, m.get("name"))
                if key in TO_UNCERTAIN:
                    hit.add(key); changed = True
                    unc = dict(m, reason=TO_UNCERTAIN[key])
                    b.setdefault("uncertain", [])
                    if not any(isinstance(u, dict) and u.get("name") == m["name"] for u in b["uncertain"]):
                        b["uncertain"].append(unc)
                    log.append("存疑  %s / %s" % key)
                    continue
                if key in SPLIT and not any(x.get("name") == SPLIT[key][1]["name"] for x in b.get("models", [])):
                    hit.add(key); changed = True
                    new_models.extend(SPLIT[key])
                    log.append("拆分  %s / %s → %s" % (key + (" / ".join(x["name"] for x in SPLIT[key]),)))
                    continue
                if key in SPLIT:
                    hit.add(key)  # 已拆分过，保持原样
                if key in PATCH:
                    hit.add(key)
                    diff = {k: v for k, v in PATCH[key].items() if m.get(k) != v}
                    if diff:
                        changed = True
                        log.append("修改  %s / %s  %s" % (key + (", ".join("%s: %r→%r" % (k, m.get(k), v) for k, v in diff.items()),)))
                        m.update(diff)
                new_models.append(m)
            # 幂等：拆分后的新条目若已存在则去重
            seen, dedup = set(), []
            for m in new_models:
                if m["name"] in seen:
                    continue
                seen.add(m["name"]); dedup.append(m)
            b["models"] = dedup
        if changed and apply:
            dump(path, doc)
    for key in list(PATCH) + list(SPLIT) + list(TO_UNCERTAIN):
        if key not in hit:
            log.append("跳过  %s / %s（未找到，可能已处理）" % key)
    return log


def _entry_span(text, key):
    """返回 specs.js 里 "key": { ... }, 整段的 [start, end)，按大括号配对，跳过字符串。"""
    m = re.search(r'\n(\s*)"%s"\s*:\s*\{' % re.escape(key), text)
    if not m:
        return None
    i, depth, in_str = m.end() - 1, 0, None
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2; continue
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                tail = re.match(r"\s*,", text[end:])
                return m.start(), end + (tail.end() if tail else 0)
        i += 1
    return None


def fix_specs(apply):
    path = os.path.join(DATA, "specs.js")
    text, log, removed = open(path, encoding="utf-8").read(), [], {}
    for old, new in SPEC_RENAME.items():
        if '"%s":' % old in text and '"%s":' % new not in text:
            text = text.replace('"%s":' % old, '"%s":' % new, 1)
            log.append("参数改键  %s → %s" % (old, new))
    for key, why in SPEC_REMOVE.items():
        span = _entry_span(text, key)
        if not span:
            log.append("参数跳过  %s（不存在）" % key); continue
        removed[key] = {"reason": why, "raw": text[span[0]:span[1]].strip()}
        text = text[:span[0]] + text[span[1]:]
        log.append("参数删除  %s（%s）" % (key, why))
    text = re.sub(r",(\s*\}\s*\}\s*;?\s*)$", r"\1", text)  # 删最后一条时清掉悬空逗号
    if apply and (removed or log):
        with open(path + ".tmp", "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(path + ".tmp", path)
        if removed:
            bk = os.path.join(DATA, "_removed_specs_%s.json" % TODAY.replace("-", ""))
            old = load(bk) if os.path.exists(bk) else {}
            old.update(removed)
            with open(bk, "w", encoding="utf-8") as f:
                json.dump(old, f, ensure_ascii=False, indent=2)
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="写回文件（默认只预览）")
    a = ap.parse_args()
    print("== 型号表 ==");  [print("  " + x) for x in fix_brands(a.apply)]
    print("== 参数表 ==");  [print("  " + x) for x in fix_specs(a.apply)]
    print("\n已写回文件。下一步：python build_data.py --check" if a.apply else "\n（预览模式，未写文件；加 --apply 执行）")
    print("注意：specs.js 里 totalModels 会在下次参数抓取时更新；改完后记得重抓 钱江|追600。")


if __name__ == "__main__":
    sys.exit(main())
