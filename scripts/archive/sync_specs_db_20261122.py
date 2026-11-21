#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在「后台工作台」的 SQLite 里同步 2026-11-22 的参数修正（与 fix_cc_conflicts_20261122.py 配套）。

我看不到工作台的表结构，所以脚本先自动识别：
  · 单键列：某列的值形如「钱江|闪600」
  · 双列：一列存品牌名（钱江）、一列存车型名（闪600）
识别不出来就只打印表结构，不做任何修改。

用法：
    python sync_specs_db_20261122.py path/to/workbench.db            # 预览：打印将执行的 SQL
    python sync_specs_db_20261122.py path/to/workbench.db --apply    # 先备份 .bak-20261122，再在事务里执行
执行后照常从工作台导出 specs.js，再跑 node tools/check_specs.js。
"""
# ---- 已归档：此脚本已执行过，数据已落库。重跑可能覆盖之后的人工修改。----
# 原用途：工作台 SQLite 同步（已于 2026-11-22 手动完成；该脚本识别不了按 model_id 关联的表结构）
import os as _os, sys as _sys
if _os.environ.get("RUN_ARCHIVED") != "1":
    _sys.exit("已归档的一次性脚本，默认不执行；确需重跑请设 RUN_ARCHIVED=1")
# ---------------------------------------------------------------------
import argparse, shutil, sqlite3, sys

RENAME = [("钱江", "闪600", "闪600 V4")]          # 原参数实为 V4 版本，跟随型号表拆分改名
DELETE = [
    ("钱江", "追600"),            # 抓成了追600RS，需重抓
    ("力帆", "K19"),              # 150cc 青春版
    ("赛科龙", "RT450"),          # 车型移入存疑
    ("香帅机车", "欧若拉400T"),   # 车型移入存疑
    ("长江摩托", "长江750 CJ750"),# 抓成经典复刻 749cc 版
    ("钱江", "鸿350GS"),          # 参数 350cc，官网实为 330cc，需重抓
    ("钱江", "SRT450"),           # 车型移入存疑
]
PROBE = ("钱江", "赛250")        # 一定存在的条目，用来识别列


def q(name):
    return '"%s"' % name.replace('"', '""')


def detect(con):
    """返回 [(table, mode, cols)]，mode = 'key'(单列 品牌|车型) 或 'pair'(品牌列, 车型列)。"""
    found = []
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for t in tables:
        cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % q(t))]
        text_cols = cols
        key_col = brand_col = model_col = None
        for c in text_cols:
            try:
                if con.execute("SELECT 1 FROM %s WHERE %s = ? LIMIT 1" % (q(t), q(c)), ("%s|%s" % PROBE,)).fetchone():
                    key_col = c
                if con.execute("SELECT 1 FROM %s WHERE %s = ? LIMIT 1" % (q(t), q(c)), (PROBE[0],)).fetchone():
                    brand_col = brand_col or c
                if con.execute("SELECT 1 FROM %s WHERE %s = ? LIMIT 1" % (q(t), q(c)), (PROBE[1],)).fetchone():
                    model_col = model_col or c
            except sqlite3.Error:
                pass
        if key_col:
            found.append((t, "key", (key_col,)))
        elif brand_col and model_col and brand_col != model_col:
            # 必须同一行同时命中，才算这张表按（品牌, 车型）存参数
            if con.execute("SELECT 1 FROM %s WHERE %s=? AND %s=? LIMIT 1" % (q(t), q(brand_col), q(model_col)), PROBE).fetchone():
                found.append((t, "pair", (brand_col, model_col)))
    return found


def plan(con, t, mode, cols):
    ops = []
    def where(b, m):
        if mode == "key":
            return "%s = ?" % q(cols[0]), ("%s|%s" % (b, m),)
        return "%s = ? AND %s = ?" % (q(cols[0]), q(cols[1])), (b, m)
    for b, old, new in RENAME:
        w, p = where(b, old)
        n = con.execute("SELECT COUNT(*) FROM %s WHERE %s" % (q(t), w), p).fetchone()[0]
        w2, p2 = where(b, new)
        exists = con.execute("SELECT COUNT(*) FROM %s WHERE %s" % (q(t), w2), p2).fetchone()[0]
        if n and not exists:
            if mode == "key":
                ops.append(("UPDATE %s SET %s = ? WHERE %s" % (q(t), q(cols[0]), w), ("%s|%s" % (b, new),) + p, "改名 %s|%s → %s" % (b, old, new)))
            else:
                ops.append(("UPDATE %s SET %s = ? WHERE %s" % (q(t), q(cols[1]), w), (new,) + p, "改名 %s|%s → %s" % (b, old, new)))
        else:
            ops.append((None, None, "跳过改名 %s|%s（%s）" % (b, old, "目标已存在" if exists else "源不存在，可能已处理")))
    for b, m in DELETE:
        w, p = where(b, m)
        n = con.execute("SELECT COUNT(*) FROM %s WHERE %s" % (q(t), w), p).fetchone()[0]
        if n:
            ops.append(("DELETE FROM %s WHERE %s" % (q(t), w), p, "删除 %s|%s（%d 行）" % (b, m, n)))
        else:
            ops.append((None, None, "跳过删除 %s|%s（不存在）" % (b, m)))
    return ops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    hits = detect(con)
    if not hits:
        print("没识别出存参数的表。表结构如下，请把它发给我，我按实际结构写 SQL：")
        for (sql,) in con.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
            print(sql)
        return 2
    allops = []
    for t, mode, cols in hits:
        print("识别到：表 %s，%s %s" % (t, "单键列" if mode == "key" else "品牌/车型两列", "/".join(cols)))
        ops = plan(con, t, mode, cols)
        for sql, params, desc in ops:
            print("  " + desc)
            if sql:
                print("    " + sql + "   -- 参数 " + repr(params))
        allops += [o for o in ops if o[0]]
    print("\n注意：如果有其他表用外键引用这些行（例如参数历史表），请先确认是否需要级联删除。")
    if not a.apply:
        print("（预览模式，未改动数据库；加 --apply 执行）")
        return 0
    bak = a.db + ".bak-20261122"
    con.close()
    shutil.copy2(a.db, bak)
    con = sqlite3.connect(a.db)
    with con:   # 单个事务：任一步失败整体回滚
        for sql, params, _ in allops:
            con.execute(sql, params)
    print("已执行 %d 条语句，原库备份在 %s" % (len(allops), bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
