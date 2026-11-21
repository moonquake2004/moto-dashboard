#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把已执行过的一次性数据脚本归档到 scripts/archive/，并在每个脚本开头加「已归档」保护。

用法（仓库根目录）：
    python scripts/archive_oneoffs.py           # 预览
    python scripts/archive_oneoffs.py --apply   # 用 git mv 移动并加保护头
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONE_OFFS = {
    "scripts/add_models.py": "方案A：批量补型号缺口（P0+P1）",
    "scripts/add_p2.py": "P2 待核实品牌补全",
    "scripts/fix_re_changjiang.py": "royal-enfield note 更正 + changjiang 存疑细化（重跑会覆盖 changjiang.uncertain）",
    "scripts/round2.py": "8 品牌 Logo 补抓第二轮（文档里路径写成了 assets/round2.py）",
    "scripts/fix_cc_conflicts_20261122.py": "2026-11-22 排量冲突修正",
}
GUARD = (
    "# ---- 已归档：此脚本已执行过，数据已落库。重跑可能覆盖之后的人工修改。----\n"
    "# 原用途：{why}\n"
    "import os as _os, sys as _sys\n"
    "if _os.environ.get(\"RUN_ARCHIVED\") != \"1\":\n"
    "    _sys.exit(\"已归档的一次性脚本，默认不执行；确需重跑请设 RUN_ARCHIVED=1\")\n"
    "# ---------------------------------------------------------------------\n"
)
README = (
    "# 已归档的一次性脚本\n\n"
    "这里的脚本都已执行过，结果已写进 `data/brands_*.json` / `data/logos.json`，保留它们只为追溯数据从哪来。\n"
    "默认运行会直接退出；确需重跑请设 `RUN_ARCHIVED=1`，并先确认不会覆盖之后的人工修改。\n\n"
    "| 脚本 | 原用途 |\n|---|---|\n"
)
TRIPLE = ('"' * 3, "'" * 3)


def insert_guard(text, why):
    """在 shebang / 编码声明 / 模块 docstring / __future__ 之后插入保护头；已插过则原样返回。"""
    if "已归档：此脚本已执行过" in text:
        return text
    lines = text.splitlines(True)
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i][:30]):
        i += 1
    if i < len(lines) and lines[i].lstrip().startswith(TRIPLE):
        q = lines[i].lstrip()[:3]
        if lines[i].count(q) >= 2:
            i += 1
        else:
            i += 1
            while i < len(lines) and q not in lines[i]:
                i += 1
            i += 1
    if i < len(lines) and lines[i].startswith("from __future__"):
        i += 1
    return "".join(lines[:i]) + GUARD.replace('{why}', why) + "".join(lines[i:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    dst_dir = os.path.join(ROOT, "scripts", "archive")
    rows = []
    for rel, why in ONE_OFFS.items():
        src = os.path.join(ROOT, rel)
        dst = os.path.join(dst_dir, os.path.basename(rel))
        if not os.path.exists(src):
            print("跳过 %s（不存在或已归档）" % rel)
            if os.path.exists(dst):
                rows.append((os.path.basename(rel), why))
            continue
        print("归档 %s → scripts/archive/%s" % (rel, os.path.basename(rel)))
        rows.append((os.path.basename(rel), why))
        if a.apply:
            os.makedirs(dst_dir, exist_ok=True)
            subprocess.run(["git", "mv", src, dst], cwd=ROOT, check=True)
            with open(dst, encoding="utf-8") as f:
                t = f.read()
            with open(dst, "w", encoding="utf-8") as f:
                f.write(insert_guard(t, why))
    if a.apply and rows:
        # 归档后 `from _jsonio import save` 的同目录导入会断，放一个转发模块
        shim = os.path.join(dst_dir, "_jsonio.py")
        if not os.path.exists(shim):
            with open(shim, "w", encoding="utf-8") as f:
                f.write(
                    "import os, sys\n"
                    "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
                    "from _jsonio import load, save  # noqa: E402,F401\n"
                )
        with open(os.path.join(dst_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(README + "".join("| `%s` | %s |\n" % r for r in rows))
    print("\n已归档，记得 git commit。" if a.apply else "\n（预览模式；加 --apply 执行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
