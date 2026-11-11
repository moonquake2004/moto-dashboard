# -*- coding: utf-8 -*-
"""方案A补完后的 P2 待核实品牌核查补全：kymco/bmw/shineray/ducati/husqvarna + loncin 定论。
仅追加经官方/摩托范/懂车帝核实的当前在售 >=250cc 缺口；自动跳过已存在重名；不新建品牌。
"""
import json, glob, os

DATA = os.path.join(os.path.dirname(__file__), "data")

# 待补型号（来源已核实）
ADD = {
    "kymco": [
        {"name": "CV3", "cc": 550, "type": "倒三轮", "price": "27800~29800元",
         "source": "https://www.kymco.com.cn/product_details_cv3.html"},
    ],
    "bmw": [
        {"name": "G 310 GS", "cc": 310, "type": "拉力ADV", "price": "52900~53900元",
         "source": "https://www.58moto.com/good/5621.html"},
        {"name": "F 900 XR", "cc": 895, "type": "旅行", "price": "126900~139900元",
         "source": "https://m.58moto.com/brand/24"},
        {"name": "S 1000 XR", "cc": 1000, "type": "旅行", "price": "233900~269900元",
         "source": "https://www.58moto.com/good/5522/configuration.html"},
    ],
    "shineray": [
        {"name": "X-Tricker魔术师", "cc": 250, "type": "越野", "price": "9680元",
         "source": "https://www.58moto.com/good/5783/configuration.html"},
    ],
    "ducati": [
        {"name": "Hypermotard 698 Mono", "cc": 659, "type": "其他", "price": None,
         "source": "https://m.lianglunshijie.com/htmlry/cpkd/146547.html"},
    ],
    "husqvarna": [
        {"name": "Svartpilen 401", "cc": 373, "type": "街车", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/naked/svartpilen/svartpilen-401-2021.html"},
        {"name": "Vitpilen 401", "cc": 373, "type": "街车", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/naked/vitpilen/vitpilen-401-2021.html"},
        {"name": "Svartpilen 801", "cc": 799, "type": "街车", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/naked.html"},
        {"name": "Vitpilen 801", "cc": 799, "type": "街车", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/news/vitpilen-801-from-husqvarna-mobility-.html"},
        {"name": "701 Enduro", "cc": 693, "type": "拉力ADV", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/news/701-enduro-701-supermoto-2026.html"},
        {"name": "701 Supermoto", "cc": 693, "type": "其他", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/supermoto/701-supermoto-2026.html"},
        {"name": "TE 250", "cc": 249, "type": "越野", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/enduro/2-stroke/te-250-2023.html"},
        {"name": "TE 300", "cc": 293, "type": "越野", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/enduro/2-stroke/te-300-2027.html"},
        {"name": "FE 250", "cc": 250, "type": "越野", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/enduro/4-stroke/fe-250-2023.html"},
        {"name": "FS 450", "cc": 450, "type": "越野", "price": None,
         "source": "https://www.husqvarna-motorcycles.com/en-cn/models/supermoto.html"},
    ],
}

# 定位每个品牌所在文件
def locate(bid):
    for path in sorted(glob.glob(os.path.join(DATA, "brands_*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        for b in doc["brands"]:
            if b["id"] == bid:
                return path, doc, b
    return None, None, None

total_added = 0
for bid, models in ADD.items():
    path, doc, brand = locate(bid)
    if not brand:
        print(f"!! 未找到品牌 {bid}，跳过")
        continue
    have = {m["name"].strip().lower() for m in brand.get("models", [])}
    added = 0
    for m in models:
        if m["name"].strip().lower() in have:
            print(f"  跳过已存在: {bid} / {m['name']}")
            continue
        brand.setdefault("models", []).append(m)
        have.add(m["name"].strip().lower())
        added += 1
        total_added += 1
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  +{added} {bid} (现 {len(brand['models'])}) -> {os.path.basename(path)}")

# loncin 维持 0，加说明
path, doc, brand = locate("loncin")
if brand:
    brand["note"] = ("隆鑫通用动力消费摩托车品牌已统一为 VOGE 无极（已单列 15 款）。"
                     "经核查，LONCIN 本品牌当前在中国市场无独立在售的 ≥250cc 两轮摩托车"
                     "（历史 LX650/CR9 已于 2019 年停产停售，现主推全地形车 ATV），故本表为 0 款。")
    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("  loncin note set (维持 0 款)")

print(f"\n合计新增: {total_added} 款")
