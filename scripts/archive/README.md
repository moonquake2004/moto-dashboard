# 已归档的一次性脚本

这里的脚本都已执行过，结果已写进 `data/brands_*.json` / `data/logos.json`，保留它们只为追溯数据从哪来。
默认运行会直接退出；确需重跑请设 `RUN_ARCHIVED=1`，并先确认不会覆盖之后的人工修改。

| 脚本 | 原用途 |
|---|---|
| `add_models.py` | 方案A：批量补型号缺口（P0+P1） |
| `add_p2.py` | P2 待核实品牌补全 |
| `fix_re_changjiang.py` | royal-enfield note 更正 + changjiang 存疑细化（重跑会覆盖 changjiang.uncertain） |
| `round2.py` | 8 品牌 Logo 补抓第二轮（文档里路径写成了 assets/round2.py） |
| `fix_cc_conflicts_20261122.py` | 2026-11-22 排量冲突修正 |
| `sync_specs_db_20261122.py` | 工作台 SQLite 同步（已手动完成，脚本不适用于本工作台表结构） |
