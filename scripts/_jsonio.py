# -*- coding: utf-8 -*-
"""数据文件读写小工具：写入走临时文件 + 原子替换，避免写一半把数据文件截断。"""
import json
import os


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, doc):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
