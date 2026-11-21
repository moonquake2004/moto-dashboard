# -*- coding: utf-8 -*-
"""合并四组品牌调研数据 + Logo 映射，生成看板数据源。

用法：
    python build_data.py           # 校验 + 生成 data/dashboard.json、data/dashboard.js
    python build_data.py --check   # 只校验，不写文件（CI 用）

校验不通过会打印全部问题并以退出码 1 结束，避免坏数据被发布。
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


def write_text(path, text):
    """写文件时沿用原文件的换行风格，避免每次重建都把整个 JSON 变成全文件 diff。"""
    nl = "\n"
    if os.path.exists(path):
        with open(path, "rb") as f:
            head = f.read(4096)
        if b"\r\n" in head:
            nl = "\r\n"
    data = text.replace("\n", nl).encode("utf-8")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)

# 白色/浅色字标：在浅色页面需要深色底衬托
DARK_LOGO_IDS = {"aprilia", "cyclone", "benda", "shineray", "kymco",
                 "peugeot-motocycles", "piaggio-vespa", "triumph", "zontes"}

# 非官方渠道在售（平行进口/小贸）：只做展示，不计入「在售」统计口径
PARALLEL_IMPORT_IDS = {"royal-enfield"}

GROUP_TO_CATEGORY = {
    "国产头部": "国产自主",
    "国产新锐及其他": "国产自主",
    "合资及台系": "合资及台系",
    "进口大贸": "进口大贸",
}

# 注意：不能用 GROUP_TO_CATEGORY.values() 求索引，其键与值存在重名，
# 会导致「国产自主」被判为未知而排到最后。
CATEGORY_ORDER = {"国产自主": 0, "合资及台系": 1, "进口大贸": 2}

# 部分品牌没有本主体的独立消费品牌 Logo，用的是集团/旗下品牌标识，需在页面标注
LOGO_NOTES = {
    "daye": "展示的是旗下启典 KIDEN 品牌标识；广东大冶为企业主体，无独立消费品牌图形标。",
    "loncin": "隆鑫通用 LONCIN 企业标识；其中大排量两轮整车业务在 VOGE 无极品牌下。",
}

# 排量口径：按官方标称值，250 整（实际 246–249cc）允许收录
CC_MIN, CC_MAX = 245, 3000

BUCKETS = ["250-399cc", "400-699cc", "700-999cc", "1000cc以上", "未标注"]


def bucket(cc):
    if not isinstance(cc, int):
        return "未标注"
    if cc < 400:
        return "250-399cc"
    if cc < 700:
        return "400-699cc"
    if cc < 1000:
        return "700-999cc"
    return "1000cc以上"


def parse_price(text):
    """把各种价格写法归一成结构化字段，供后续排序/筛选使用。

    支持 "15999元" / "28999元起" / "16680~22980元" / "21.88~23.88万元"。
    返回 {"min": int, "max": int, "from": bool, "unit": "元"|"万元"}，无法解析返回 None。
    """
    if not text:
        return None
    s = str(text).strip()
    for ch in ("￥", "¥", ",", "，", " "):
        s = s.replace(ch, "")
    for ch in ("～", "－", "–", "—"):
        s = s.replace(ch, "~")
    mult = 10000 if "万" in s else 1
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None
    vals = [int(round(float(n) * mult)) for n in nums]
    return {"min": min(vals), "max": max(vals), "from": "起" in s,
            "unit": "万元" if mult > 1 else "元"}



from urllib.parse import urlparse

PRICE_MIN_YUAN, PRICE_MAX_YUAN = 8000, 1000000   # 250cc+ 合理指导价范围
SPEC_CC_TOL = 0.05        # 参数表排量与型号表偏差 >5% 视为抓错版本
SPEC_CC_ABS = 15          # 且绝对差 >15cc（避免 1043 vs 1000 这类标称取整误报）
SPEC_PRICE_TOL = 0.20     # 参数版本价格偏离指导价区间 >20% 告警
SPEC_CC_IGNORE = set()    # 已人工确认的「品牌|车型」白名单，如 {"川崎|Z1000"}
YEAR_IN_NAME = re.compile(r"20\d\d\s*款|（含|\(含")


def load_specs(path):
    """解析 data/specs.js（JS 对象字面量，键不带引号、可能有尾逗号）。"""
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    body = text.split("=", 1)[1].strip().rstrip(";")
    body = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', body)   # 给裸键加引号
    body = re.sub(r",(\s*[}\]])", r"\1", body)                       # 去尾逗号
    try:
        return json.loads(body).get("models", {})
    except ValueError as e:
        raise SystemExit("specs.js 解析失败：%s" % e)


def _num(v):
    m = re.search(r"\d+(?:\.\d+)?", str(v).replace(",", "")) if v not in (None, "") else None
    return float(m.group()) if m else None


def validate_extra(brands, specs, errors, warnings):
    model_keys = set()
    for b in brands:
        for m in b["models"]:
            key = "%s|%s" % (b["name"], m["name"])
            model_keys.add(key)
            tag = "%s: %r" % (b["id"], m["name"])

            # 1) 价格范围：防 parse_price 把年款/多段价格解析出离谱值
            if m["priceMin"] is not None:
                if not (PRICE_MIN_YUAN <= m["priceMin"] <= PRICE_MAX_YUAN):
                    errors.append("%s 价格超出合理范围 %r → %s 元" % (tag, m["price"], m["priceMin"]))
                if m["priceMax"] and m["priceMax"] > m["priceMin"] * 2.5:
                    warnings.append("%s 价格区间过宽 %r，检查是否混入其他车型" % (tag, m["price"]))
            if m["price"] and re.search(r"20\d\d\s*(?:年|款)", m["price"]):
                errors.append("%s 价格文本含年份 %r，会被误解析" % (tag, m["price"]))

            # 2) 型号名不应带年款/配置说明（口径：年款不单列）
            if YEAR_IN_NAME.search(m["name"]):
                warnings.append("%s 型号名含年款/配置说明，建议移到备注" % tag)

            # 3) 来源质量：必须 https，且不能只是官网首页
            src = m.get("source") or ""
            if src:
                u = urlparse(src)
                if u.scheme != "https":
                    warnings.append("%s 来源非 https：%s" % (tag, src))
                if u.path in ("", "/") and not u.query:
                    warnings.append("%s 来源只是首页，无法逐条核实：%s" % (tag, src))

            # 4) 参数表交叉校验
            s = specs.get(key)
            if not s or key in SPEC_CC_IGNORE:
                continue
            scc = _num(s.get("cc"))
            if scc and m["cc"]:
                diff = abs(scc - m["cc"])
                # 参数表 cc 恰好等于车名里的数字（如 CM500 实际 471cc）→ 只是标称名，降为告警
                nominal = str(int(scc)) in re.findall(r"\d{3,4}", m["name"] + " " + str(s.get("variant", "")))
                if diff > SPEC_CC_ABS and diff / m["cc"] > SPEC_CC_TOL:
                    (warnings if nominal else errors).append("%s 参数排量 %scc ≠ 型号表 %scc（疑似抓错版本：%s）"
                                  % (tag, int(scc), m["cc"], s.get("variant", "")))
                if scc < 245:
                    errors.append("%s 参数排量 %scc < 250，可能不属于收录口径" % (tag, int(scc)))
            sp = _num(s.get("price"))
            if sp and m["priceMin"]:
                lo = m["priceMin"] * (1 - SPEC_PRICE_TOL)
                hi = (m["priceMax"] or m["priceMin"]) * (1 + SPEC_PRICE_TOL)
                if not lo <= sp <= hi:
                    warnings.append("%s 参数版本价 %s 偏离指导价 %r（参数可能来自其他配置）"
                                    % (tag, s.get("price"), m["price"]))
            for f in ("kw", "nm", "weight", "tank", "wb"):
                if s.get(f) is not None and not isinstance(s[f], (int, float)):
                    errors.append("%s 参数 %s 不是数值：%r（会破坏最优值比较）" % (tag, f, s[f]))
            w = s.get("weight")
            if isinstance(w, (int, float)) and not 100 <= w <= 600:
                warnings.append("%s 整备质量 %s kg 异常" % (tag, w))

    # 5) 孤儿参数：键对不上，前端永远显示不出来
    for k in specs:
        if k not in model_keys:
            errors.append("specs.js 键 %r 在型号表中不存在" % k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    ap.add_argument("--strict", action="store_true", help="告警也视为失败")
    args = ap.parse_args()

    logos = json.load(open(os.path.join(DATA, "logos.json"), encoding="utf-8"))
    brands = []
    errors = []
    warnings = []

    for path in sorted(glob.glob(os.path.join(DATA, "brands_*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        group = doc.get("group", "")
        if group not in GROUP_TO_CATEGORY:
            errors.append("%s: 未知分组 %r" % (os.path.basename(path), group))
        for b in doc["brands"]:
            bid = b.get("id")
            if not bid:
                errors.append("%s: 品牌缺少 id（%r）" % (os.path.basename(path), b.get("name")))
            models = []
            seen_names = set()
            for m in b.get("models", []):
                name = (m.get("name") or "").strip()
                if not name:
                    errors.append("%s: %s 有型号缺 name" % (bid, b.get("name")))
                    continue
                key = name.lower()
                if key in seen_names:
                    errors.append("%s: 型号重复 %r" % (bid, name))
                seen_names.add(key)

                cc = m.get("cc")
                if cc is None:
                    warnings.append("%s: %r 缺 cc（会计入「未标注」）" % (bid, name))
                elif not isinstance(cc, int) or not (CC_MIN <= cc <= CC_MAX):
                    errors.append("%s: %r cc 异常 %r（应在 %d–%d）" % (bid, name, cc, CC_MIN, CC_MAX))
                    cc = None

                price_text = m.get("price") or None
                price = parse_price(price_text)
                if price_text and not price:
                    errors.append("%s: %r 价格无法解析 %r" % (bid, name, price_text))

                if not (m.get("type") or "").strip():
                    errors.append("%s: %r 缺车型类别" % (bid, name))
                if not m.get("source"):
                    errors.append("%s: %r 缺核实来源 source" % (bid, name))

                models.append({
                    "name": name,
                    "cc": cc,
                    "type": (m.get("type") or "未分类").strip(),
                    "price": price_text,
                    "priceMin": price["min"] if price else None,
                    "priceMax": price["max"] if price else None,
                    "priceFrom": bool(price["from"]) if price else False,
                    "priceUnit": price["unit"] if price else None,
                    "source": m.get("source") or None,
                    "bucket": bucket(cc),
                })

            lg = logos.get(bid, {})
            logo_file = lg.get("file") if lg.get("status") == "ok" else None
            if logo_file and not os.path.exists(os.path.join(BASE, logo_file)):
                errors.append("%s: logo 文件不存在 %s" % (bid, logo_file))
                logo_file = None

            brands.append({
                "id": bid,
                "name": b.get("name") or bid,
                "nameEn": b.get("nameEn") or "",
                "company": b.get("company") or "",
                "category": GROUP_TO_CATEGORY.get(group, group),
                "subCategory": b.get("category") or GROUP_TO_CATEGORY.get(group, ""),
                "group": group,
                "marketStatus": "parallel" if bid in PARALLEL_IMPORT_IDS else "official",
                "website": b.get("website") or None,
                "logo": {
                    "file": logo_file,
                    "status": lg.get("status", "missing"),
                    "source": lg.get("source") or None,
                    "note": LOGO_NOTES.get(bid),
                },
                "logoDark": bid in DARK_LOGO_IDS and bool(logo_file),
                "models": models,
                "modelCount": len(models),
                "uncertain": b.get("uncertain", []),
                "sources": b.get("sources", []),
                "note": b.get("note") or "",
            })

    # 唯一性校验
    id_counts = Counter(b["id"] for b in brands)
    for k, v in id_counts.items():
        if v > 1:
            errors.append("品牌 id 重复：%s（%d 次）" % (k, v))
    name_counts = Counter(b["name"] for b in brands)
    for k, v in name_counts.items():
        if v > 1:
            warnings.append("品牌名重复：%s（%d 次）" % (k, v))

    # 增强校验：价格范围 / 来源质量 / 参数表与型号表交叉核对
    specs = load_specs(os.path.join(DATA, "specs.js"))
    validate_extra(brands, specs, errors, warnings)

    if errors:
        print("数据校验失败，共 %d 项：" % len(errors))
        for e in errors:
            print("  ✗ " + e)
        return 1
    if warnings:
        print("数据校验告警（不阻断）：")
        for w in warnings:
            print("  ! " + w)
        if args.strict:
            print("--strict：告警视为失败")
            return 1

    brands.sort(key=lambda x: (CATEGORY_ORDER.get(x["category"], 9),
                               -x["modelCount"], x["name"]))

    official = [b for b in brands if b["marketStatus"] == "official"]
    all_models = [m for b in official for m in b["models"]]
    parallel_models = [m for b in brands if b["marketStatus"] == "parallel" for m in b["models"]]

    by_cat = Counter(b["category"] for b in brands)
    by_cat_models = Counter()
    for b in official:
        by_cat_models[b["category"]] += b["modelCount"]
    by_bucket = Counter(m["bucket"] for m in all_models)
    by_type = Counter(m["type"] for m in all_models)

    market = {
        "year": 2025,
        "source": "中国摩托车商会《产销快讯》、中国证券报 2026-04-18 隆鑫通用年报摘要、广发证券摩托车行业报告",
        "items": [
            {"label": "250cc以上销量", "value": "95.23", "unit": "万辆", "delta": "+25.87%", "note": "2025年全年"},
            {"label": "500cc以上销量", "value": "20.91", "unit": "万辆", "delta": "+107.56%", "note": "增长最快细分"},
            {"label": "250cc+出口增速", "value": "48.47", "unit": "%", "delta": "", "note": "出口为主要驱动"},
            {"label": "大排量内销CR3", "value": "50.5", "unit": "%", "delta": "", "note": "春风22.8%/钱江15.5%/隆鑫12.2%"},
        ],
        "leaders250": ["春风动力", "隆鑫通用", "钱江摩托", "土星动力", "宗申集团"],
        "leaders500": ["隆鑫通用", "春风动力", "钱江摩托", "广东大冶", "土星动力"],
        "leadersSource": "中国摩托车商会，2025年250cc以上/500cc以上摩托车销量前五企业",
    }

    out = {
        "meta": {
            "title": "国内250cc以上摩托车厂商品牌看板",
            "updated": "2026-11-10",
            "scope": "中国市场在售 · 排量 ≥250cc · 各品牌官网/官方渠道当前在售车型",
            "principles": [
                "只收录可在品牌中国官网、官方商城或权威车型库（摩托范/懂车帝）核实的在售车型，不虚构型号",
                "同系列不同版本合并为一条主型号，年款（2026款/2027款）不单列",
                "250cc 整（实际 246–249cc）按 ≥250cc 口径收录",
                "官方指导价未公布或未能核实的记「—」，不做估算",
                "Logo 均为品牌官方图片，未获取到的品牌以品牌标准字兜底并明确标注",
            ],
            "sources": [
                "各品牌中国官网车型页 / 官方价目表",
                "摩托范 58moto.com 品牌在售车型库",
                "懂车帝摩托车型参数页",
                "中国摩托车商会《产销快讯》",
                "中国证券报、广发证券摩托车行业研究报告",
            ],
        },
        "stats": {
            "brandCount": len(brands),
            "brandCountWithModels": sum(1 for b in official if b["modelCount"] > 0),
            "modelCount": len(all_models),
            "modelCountAll": len(all_models) + len(parallel_models),
            "parallelBrandCount": sum(1 for b in brands if b["marketStatus"] == "parallel"),
            "parallelModelCount": len(parallel_models),
            "logoCount": sum(1 for b in brands if b["logo"]["file"]),
            "logoMissing": sum(1 for b in brands if not b["logo"]["file"]),
            "byCategory": dict(by_cat),
            "byCategoryModels": dict(by_cat_models),
            "byBucket": dict(by_bucket),
            "byType": dict(by_type),
        },
        "market": market,
        "brands": brands,
    }

    if args.check:
        print("校验通过：%d 品牌 / %d 在售型号（另有 %d 款平行进口未计入）"
              % (out["stats"]["brandCount"], out["stats"]["modelCount"],
                 out["stats"]["parallelModelCount"]))
        return 0

    write_text(os.path.join(DATA, "dashboard.json"),
               json.dumps(out, ensure_ascii=False, indent=2))
    write_text(os.path.join(DATA, "dashboard.js"),
               "window.MOTO_DATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

    print("brands:", len(brands), "models:", len(all_models),
          "(+%d parallel)" % len(parallel_models),
          "logos:", out["stats"]["logoCount"])
    print("byCategory:", dict(by_cat_models))
    print("byBucket:", dict(by_bucket))
    print("byType:", dict(by_type))
    return 0


if __name__ == "__main__":
    sys.exit(main())
