# -*- coding: utf-8 -*-
"""修正 royal-enfield 误导note（未官方入华，价格维持占位）；细化 changjiang Bobbie 变体 uncertain。"""
import json, glob, os

DATA = os.path.join(os.path.dirname(__file__), "data")

def locate(bid):
    for path in sorted(glob.glob(os.path.join(DATA, "brands_*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        for b in doc["brands"]:
            if b["id"] == bid:
                return path, doc, b
    return None, None, None

# --- royal-enfield: 更正 note，价格维持 null ---
p, doc, re = locate("royal-enfield")
re["note"] = ("皇家恩菲尔德(Royal Enfield)截至2026-11尚未以官方大贸身份正式进入中国大陆市场，"
              "仅在台湾地区由太古汽车于2025-12引进（官方指导价为新台币NTD，非人民币）。"
              "大陆市场可见车辆多为平行进口(小贸)，无统一官方人民币指导价，故本表14款价格均以「—」(null)占位，不作估算。"
              "下列型号为RE全球在售真实车系；是否保留本品牌（平行进口在售）由看板维护者决定。")
# 价格维持 null（不编造）
json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("royal-enfield note 已更正（价格维持 null）")

# --- changjiang: 细化 Bobbie 变体 uncertain（真实在售但版本繁杂，暂不升为确认型号）---
p, doc, cj = locate("changjiang")
SRC = "https://www.58moto.com/brand/H-296.html"
SRC2 = "https://www.lianglunshijie.com/brand/58/"
new_unc = [
    {"name": "长江750 CJ750 实际排量", "cc": None, "type": "边三轮", "price": None,
     "source": "https://m.sohu.com/a/242756923_608091",
     "reason": "复活版长江750型号名含750，实际搭载春风650cc并列双缸发动机（型号名为历史系列名），本条cc按实际650cc记并在此说明"},
    {"name": "Bobbie 400 II (两轮版)", "cc": 400, "type": "巡航", "price": "28800~30800元",
     "source": SRC, "reason": "Bobbie系列两轮巡航版，与已收录Bobbie 400(28800)为同系年款/配置差异，是否作为独立型号待定"},
    {"name": "Bobbie II 450S", "cc": 450, "type": "巡航", "price": "30980~32980元",
     "source": SRC, "reason": "Bobbie 450 系列在售，未作为独立型号收录，待定"},
    {"name": "Bobbie III 450S", "cc": 450, "type": "巡航", "price": "38888~43880元",
     "source": SRC, "reason": "Bobbie 450 高配在售，未收录，待定"},
    {"name": "Bobbie 400 III (边三轮版)", "cc": 400, "type": "边三轮", "price": "42800~44300元",
     "source": SRC, "reason": "带边斗版本，与两轮Bobbie 400区分，待定"},
    {"name": "Bobbie ll 700i", "cc": 700, "type": "巡航", "price": "38880~41880元",
     "source": SRC, "reason": "与已收录Bobbie 700(38880)同系，待定"},
    {"name": "Bobbie III 700i", "cc": 700, "type": "巡航", "price": "47777~62880元",
     "source": SRC2, "reason": "Bobbie 700 高配/定制版，未收录，待定"},
    {"name": "Bobbie 650 III", "cc": 650, "type": "巡航", "price": "53800~55800元",
     "source": SRC, "reason": "Bobbie 650 在售，未收录，待定"},
    {"name": "CJ 650 两轮版", "cc": 650, "type": "巡航", "price": "39800~40800元",
     "source": SRC, "reason": "CJ650 两轮版（非边三轮），与已收录边三轮CJ650区分，待定"},
]
cj["uncertain"] = new_unc
json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"changjiang uncertain 已细化为 {len(new_unc)} 条（含CJ750说明）")
