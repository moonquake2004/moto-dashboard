# -*- coding: utf-8 -*-
"""方案A：批量补已确认的型号缺口（P0+P1），跳过已有重复项。"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# 追加清单：brand_id -> [ {name, cc, type, price(str|None), source} ]
ADD = {
    # ---- 国产新锐及其他 (brands_b) ----
    "benda": [
        {"name": "灰石250CVT", "cc": 249, "type": "巡航", "price": "18980元", "source": "https://www.bendamotor.cn/Seek/page/9"},
        {"name": "黑旗500", "cc": 496, "type": "巡航", "price": "33800元", "source": "https://www.bendamotor.cn/Seek/page/9"},
    ],
    "kove": [
        {"name": "625X", "cc": 581, "type": "拉力ADV", "price": "31777元", "source": "https://m.58moto.com/brand/206"},
        {"name": "650RR", "cc": 650, "type": "仿赛", "price": "33977元", "source": "https://m.58moto.com/brand/206"},
    ],
    "lifan": [
        {"name": "K19", "cc": 250, "type": "巡航", "price": "13980元", "source": "https://www.58moto.com/merchant/car/265147?id=17"},
    ],
    "daye": [
        {"name": "启典 ZT250-R", "cc": 249, "type": "街车", "price": None, "source": "https://www.kiden.cn/ch/products/ModelsDetailed.aspx?Cid=2EDE22E721F7BC97"},
        {"name": "启典 KD250-V", "cc": 250, "type": "复古", "price": None, "source": "https://www.58moto.com/good/12500/configuration.html"},
        {"name": "启典 KD250-Z", "cc": 250, "type": "街车", "price": None, "source": "https://www.17vin.com/gonggao/213096/KD250Z.html"},
    ],
    "changjiang": [
        {"name": "Bobbie 400", "cc": 400, "type": "巡航", "price": "28800元", "source": "https://www.58moto.com/brand/H-296.html"},
        {"name": "Bobbie 700", "cc": 700, "type": "巡航", "price": "38880元", "source": "https://www.58moto.com/brand/H-296.html"},
    ],
    "souo": [
        {"name": "S2000C", "cc": 2000, "type": "巡航", "price": "168800元起", "source": "https://www.souomoto.com/"},
    ],
    "xiangshuai": [
        {"name": "YES418", "cc": 385, "type": "巡航", "price": "19980元起", "source": "https://www.58moto.com/article/3679/11595523.html"},
    ],
    # ---- 国产头部 (brands_a) ----
    "qjmotor": [
        {"name": "SRT450", "cc": 450, "type": "拉力ADV", "price": "27980元", "source": "https://www.58moto.com/article/114/12524891.html"},
    ],
    # ---- 合资及台系 (brands_c) ----
    "sym": [
        {"name": "CRUISYM 250 (巡弋250)", "cc": 249, "type": "踏板", "price": "21980元", "source": "https://www.xsmt.com/product/show-24036.html"},
        {"name": "剑齿虎 ADXTG 400", "cc": 399, "type": "踏板", "price": "46980元", "source": "https://www.58moto.com/article/114/12505983.html"},
        {"name": "Joymax Z 300", "cc": 278, "type": "踏板", "price": "25980元", "source": "https://m.58moto.com/brand/245"},
        {"name": "MaxSym 400", "cc": 399, "type": "踏板", "price": "52800元", "source": "https://www.lianglunshijie.com/motor/Maxsym400TCS24020/index.html"},
    ],
    # ---- 进口大贸 (brands_d) ----
    "honda": [
        {"name": "CL500", "cc": 471, "type": "复古", "price": "58800元", "source": "https://m.58moto.com/news/10692442?share=1"},
    ],
    "yamaha": [
        {"name": "MT-09 SP", "cc": 890, "type": "街车", "price": "139800元", "source": "https://www.yamaha-motor.com.cn/mc/products/mt-09sp/"},
    ],
    "kawasaki": [
        {"name": "NINJA ZX-4RR", "cc": 399, "type": "仿赛", "price": "76800元", "source": "https://www.kawasaki-motors.cn/"},
        {"name": "ELIMINATOR 500", "cc": 451, "type": "巡航", "price": "46800元", "source": "https://www.toutiao.com/a7363478304919192118"},
        {"name": "NINJA ZX-6R", "cc": 636, "type": "仿赛", "price": "109800元", "source": "https://m.toutiao.com/zixun/7534126582110177280"},
    ],
    "suzuki": [
        {"name": "Hayabusa 隼 GSX1300R", "cc": 1340, "type": "仿赛", "price": None, "source": "https://www.lianglunshijie.com/brand/299/"},
        {"name": "Burgman 400 汉堡人", "cc": 400, "type": "踏板", "price": "48000元", "source": "https://www.lianglunshijie.com/brand/299/"},
        {"name": "SV650X", "cc": 645, "type": "复古", "price": "85800元", "source": "https://www.lianglunshijie.com/brand/299/"},
    ],
    "royal-enfield": [
        {"name": "Classic 350", "cc": 349, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Meteor 350", "cc": 349, "type": "巡航", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Hunter 350", "cc": 349, "type": "街车", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Bullet 350", "cc": 349, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Goan Classic 350", "cc": 349, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Himalayan 450", "cc": 452, "type": "拉力ADV", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Guerrilla 450", "cc": 452, "type": "街车", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Interceptor 650", "cc": 648, "type": "街车", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Continental GT 650", "cc": 648, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Super Meteor 650", "cc": 648, "type": "巡航", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Shotgun 650", "cc": 648, "type": "巡航", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Bear 650", "cc": 648, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Classic 650", "cc": 648, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
        {"name": "Bullet 650", "cc": 648, "type": "复古", "price": None, "source": "https://www.royalenfield.com/"},
    ],
    "indian": [
        {"name": "CHIEF", "cc": 1890, "type": "巡航", "price": "199800元", "source": "https://www.indianmotorcycle.cn/"},
        {"name": "CHIEF DARK HORSE", "cc": 1890, "type": "巡航", "price": "246800元", "source": "https://m.autohome.com.cn/motorbike/series/10000193"},
        {"name": "CHIEF BOBBER DARK HORSE", "cc": 1890, "type": "巡航", "price": "256800元", "source": "https://m.autohome.com.cn/motorbike/series/10000193"},
        {"name": "SUPER CHIEF", "cc": 1890, "type": "巡航", "price": "269800元", "source": "https://m.autohome.com.cn/motorbike/series/10000193"},
        {"name": "SPORT CHIEF", "cc": 1890, "type": "巡航", "price": "256800元", "source": "https://m.autohome.com.cn/motorbike/series/10000193"},
    ],
    "harley-davidson": [
        {"name": "Street Glide® Limited", "cc": 1923, "type": "旅行", "price": "429800元", "source": "https://harley-davidson.cn/cn/zh/motorcycles/index.html"},
        {"name": "Road Glide® Limited", "cc": 1923, "type": "旅行", "price": "449800元", "source": "https://harley-davidson.cn/cn/zh/motorcycles/index.html"},
        {"name": "CVO™ Street Glide® ST", "cc": 1977, "type": "旅行", "price": "518800元", "source": "https://harley-davidson.cn/cn/zh/motorcycles/index.html"},
        {"name": "CVO™ Street Glide® Limited", "cc": 1977, "type": "旅行", "price": "538800元", "source": "https://harley-davidson.cn/cn/zh/motorcycles/index.html"},
        {"name": "CVO™ Street Glide® 3 Limited", "cc": 1977, "type": "倒三轮", "price": None, "source": "https://harley-davidson.cn/cn/zh/motorcycles/cvo.html"},
    ],
    "ktm": [
        {"name": "250 Duke", "cc": 249, "type": "街车", "price": "34980元", "source": "https://www.ktm.com/zh-cn/models/naked-bike/250-duke-2022.html"},
        {"name": "390 Adventure", "cc": 373, "type": "拉力ADV", "price": "53800元", "source": "https://www.ktm.com/zh-cn/models/travel/ktm-390-adventure2021.html"},
    ],
}


def main():
    files = ["brands_a.json", "brands_b.json", "brands_c.json", "brands_d.json"]
    total_added = 0
    for fn in files:
        path = os.path.join(DATA, fn)
        doc = json.load(open(path, encoding="utf-8"))
        for b in doc["brands"]:
            bid = b.get("id")
            if bid not in ADD:
                continue
            existing = {m.get("name", "").strip().lower() for m in b.get("models", [])}
            added = 0
            for m in ADD[bid]:
                if m["name"].strip().lower() in existing:
                    print(f"  SKIP dup {bid}: {m['name']}")
                    continue
                b.setdefault("models", []).append({
                    "name": m["name"], "cc": m["cc"], "type": m["type"],
                    "price": m["price"], "source": m["source"],
                })
                existing.add(m["name"].strip().lower())
                added += 1
            if added:
                total_added += added
                print(f"  +{added} {bid} (now {len(b['models'])})")
        json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("TOTAL ADDED:", total_added)


if __name__ == "__main__":
    main()
