# -*- coding: utf-8 -*-
"""合并四组品牌调研数据 + Logo 映射，生成看板数据源。"""
import json
import glob
import os
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# 白色/浅色字标：在浅色页面需要深色底衬托
DARK_LOGO_IDS = {"aprilia", "cyclone", "benda", "shineray", "kymco",
                 "peugeot-motocycles", "piaggio-vespa", "triumph", "zontes"}

GROUP_TO_CATEGORY = {
    "国产头部": "国产自主",
    "国产新锐及其他": "国产自主",
    "合资及台系": "合资及台系",
    "进口大贸": "进口大贸",
}

# 注意：不能用 GROUP_TO_CATEGORY.values() 求索引，其键与值存在重名，
# 会导致「国产自主」被判为未知而排到最后。
CATEGORY_ORDER = {"国产自主": 0, "合资及台系": 1, "进口大贸": 2}


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


def main():
    logos = json.load(open(os.path.join(DATA, "logos.json"), encoding="utf-8"))
    brands = []

    for path in sorted(glob.glob(os.path.join(DATA, "brands_*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        group = doc.get("group", "")
        for b in doc["brands"]:
            bid = b.get("id")
            models = []
            for m in b.get("models", []):
                models.append({
                    "name": m.get("name") or "未命名",
                    "cc": m.get("cc") if isinstance(m.get("cc"), int) else None,
                    "type": m.get("type") or "未分类",
                    "price": m.get("price") or None,
                    "source": m.get("source") or None,
                    "bucket": bucket(m.get("cc")),
                })
            lg = logos.get(bid, {})
            brands.append({
                "id": bid,
                "name": b.get("name") or bid,
                "nameEn": b.get("nameEn") or "",
                "company": b.get("company") or "",
                "category": GROUP_TO_CATEGORY.get(group, group),
                "subCategory": b.get("category") or GROUP_TO_CATEGORY.get(group, ""),
                "group": group,
                "website": b.get("website") or None,
                "logo": {
                    "file": lg.get("file") if lg.get("status") == "ok" else None,
                    "status": lg.get("status", "missing"),
                    "source": lg.get("source") or None,
                },
                "logoDark": bid in DARK_LOGO_IDS and lg.get("status") == "ok",
                "models": models,
                "modelCount": len(models),
                "uncertain": b.get("uncertain", []),
                "sources": b.get("sources", []),
                "note": b.get("note") or "",
            })

    brands.sort(key=lambda x: (CATEGORY_ORDER.get(x["category"], 9),
                               -x["modelCount"], x["name"]))

    all_models = [m for b in brands for m in b["models"]]
    by_cat = Counter(b["category"] for b in brands)
    by_cat_models = Counter()
    for b in brands:
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
            "updated": "2026-11-09",
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
            "modelCount": len(all_models),
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

    with open(os.path.join(DATA, "dashboard.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA, "dashboard.js"), "w", encoding="utf-8") as f:
        f.write("window.MOTO_DATA = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    print("brands:", len(brands), "models:", len(all_models),
          "logos:", out["stats"]["logoCount"])
    print("byCategory:", dict(by_cat_models))
    print("byBucket:", dict(by_bucket))
    print("byType:", dict(by_type))


if __name__ == "__main__":
    main()
