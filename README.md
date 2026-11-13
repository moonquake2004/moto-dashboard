# 国内 250cc+ 摩托车品牌看板

一个纯静态的摩托车市场看板：44 个品牌、424 款 ≥250cc 在售车型（另有 14 款平行进口单独标注、不计入统计口径），按圈层 / 排量段 / 车型类别 / 价格区间交叉筛选，可多词搜索、按价格或排量排序，附品牌墙、市场大盘、图表联动与数据口径说明。

界面为深色工业风，支持浅色主题切换、品牌收藏（存 localStorage）、品牌详情右侧抽屉；排量 / 类别 / 圈层三张条形图点击即筛到型号浏览器。价格六档按**起售价**落档，六档相加正好等于 438（含平行进口）。

「结构洞察」区把同一份数据换三种角度看：各车身类别的型号数 TOP3 品牌（渠道密度）、各价格带的型号数 TOP5 品牌（价格带覆盖）、类别 × 价格档矩阵（11 行 × 6 列，格内为该组合型号数、底色按数量深浅）。点榜上品牌或矩阵里非空格子，直接带着「类别 + 价格档」跳到型号浏览器；矩阵格相加 = 424，与统计口径一致。矩阵末行是各价格档合计、最右是各类别合计，点行合计只看类别、点列合计只看价格档、点右下角 424 清空；悬停任意一格会列出撑起这一格的品牌与款数。图表区下方还有一排 11 个车身类别图块，点一下直接筛过去。价格档是横向标签，数量直接标在标签上（1 / 47 / 80 / 82 / 182 / 46），再点一次即取消。搜索按空格分词、多词 AND，命中处全部高亮。筛选到零结果时不只报「没有」，会实时算出「清空搜索 / 去掉类别 / 去掉价格档 / 去掉排量段 / 含平行进口」各自能出多少车，点一下即放宽。

型号表首列是勾选框：攒 2–3 款后底部出现对比浮条，点「开始对比」并排看指导价、价格性质（指导价 / 起售价）、排量、车身类别、价格档、渠道口径、品牌圈层与逐条来源；最低价与最大排量标绿并打 tag，选第 4 款会被拒绝。表头在容器内固定，横向滚动时勾选列与品牌列也固定，438 行下滚到哪儿都看得见列名。品牌车库上方有 A-Z 索引（按英文名首字母，带各字母品牌数，点选即筛、再点取消）。

每个品牌还有一张独立静态页 `brand/<id>.html`（零 JS、深色主题），含型号表、价格区间、排量区间、存疑说明、同类别品牌内链与逐条来源，并带 `Brand + ItemList(Product, offers) + BreadcrumbList` 结构化数据；首页带 `WebSite + Dataset`，口径区末尾是 44 个品牌页的静态内链目录。`sitemap.xml` 覆盖首页与 44 张品牌页。

市场大盘区多了一块「250cc+ 月度产销趋势」：2026 年 1—9 月逐月产量 / 销量双柱，悬停看当月同比，数据来自中国摩托车商会逐月发布的行业运行报告，由 `scripts/fetch_monthly.py` 抓取落库到 `data/market_monthly.js`，每月商会发稿后重跑一次脚本即可。

线上站点：<https://moonquake2004.github.io/moto-dashboard/>

## 目录结构

```
index.html              单页站点（样式与逻辑内联）
build_data.py           数据构建 + 校验：data/brands_*.json → data/dashboard.js / dashboard.json
build_site.py           组装可发布站点：_site/index.html（注入版本号）+ data + assets + brand/*.html + sitemap.xml + robots.txt
data/brands_a~d.json    人工维护的原始数据（唯一的事实来源，改数据只改这里）
data/dashboard.js       构建产物，前端直接加载（window.MOTO_DATA）
data/dashboard.json     构建产物，同内容，供人/脚本查看
data/market_monthly.js  月度产销序列（scripts/fetch_monthly.py 生成，含逐月来源链接）
data/logos.json         Logo 获取情况清单
assets/logos/           本地化的品牌官方 Logo
assets/favicon.svg      站点图标
assets/publish_api.py   备用发布通道（github.com 不可达时走 api.github.com）
stats_server.py         可选：访问统计后端（Flask + SQLite）
scripts/                数据整理脚本（历史存档）+ fetch_monthly.py（商会月度稿抓取）
.github/workflows/pages.yml  校验 + 发布到 GitHub Pages
```

## 数据管线

改数据 → 构建 → 提交，三步：

```bash
# 1. 编辑 data/brands_*.json（唯一需要手改的文件）
# 2. 只校验，不写文件（CI 里也跑这一步，不通过就不会发布）
python3 build_data.py --check
# 3. 生成 data/dashboard.js 与 data/dashboard.json
python3 build_data.py
```

`build_data.py` 会做这些校验，任何一条不通过就返回非零退出码：

- 品牌 `id` 唯一、`category` / `group` / `marketStatus` 取值合法
- 同一品牌内型号不重名
- `cc` 在 245–3000 之间（250cc 整按 ≥250 口径收录，故下界放到 245）
- `price` 能被解析成数字，或为空
- `type` 非空、`source` 必填
- `logo` 指向的文件真实存在

同时自动派生：`bucket`（排量段）、`priceMin` / `priceMax` / `priceFrom` / `priceUnit`（价格结构化）、各维度统计。

## 数据字段

品牌：`id` `name` `nameEn` `company` `category` `subCategory` `group` `marketStatus` `website` `logo` `logoDark` `models` `modelCount` `uncertain` `sources` `note`

型号：`name` `cc` `type` `price`（原样展示文本）`priceMin` `priceMax` `priceFrom`（是否"起"）`priceUnit`（元/万元）`source` `bucket`

关于 `marketStatus`：

- `official` —— 以官方大贸身份在中国大陆销售的品牌，型号计入 `stats.modelCount`
- `parallel` —— 仅以平行进口方式流入（如 Royal Enfield），型号单列展示、**不计入**统计，
  前端在独立分组里呈现。`stats.modelCountAll` 是含平行进口的总数。

## 月度产销数据

```bash
python3 scripts/fetch_monthly.py --check   # 只看抓到了什么，不写文件
python3 scripts/fetch_monthly.py           # 抓取并覆盖 data/market_monthly.js
```

商会固定次月中旬发上月稿，脚本按「发布日期月份 − 1」定位数据月份，只取正文里
「（排量 250ml/250cc 以上，不含）…产销 X 万辆和 Y 万辆 … 同比 A% 和 B%」那一段，
每条记录都带原文链接。脚本自带三层自检：月份必须连续；环比幅度不得超过 80%；
单月数值超过 20 万辆直接判为「累计口径串行」丢弃（曾抓到 2023-07 的「1-6 月 30.18 万辆」）；
整年 12 个月齐了还要和商会官方年度口径（2025 年 95.37 / 95.23 万辆）对账，差超 0.6 万辆即报警。
商会站点对海外 IP 不稳，所以抓取不放进 CI，只在本地跑，提交的是数据文件。

默认 `--pages 4`、`--years 1`：只落当年序列。想做跨年对照时用 `--years 2`，但注意
2025 年 5 月与 6 月两篇原稿数字完全相同（都是 10.05 / 10.12 万辆），环比却分别写 −17.75% 和 +4.68%，
自相矛盾——跨年铺成一条线会把原稿笔误画成趋势，所以页面上只画当年逐月，年度对比放在右上角 KPI。

## 部署

推送到 `main` 即触发 GitHub Pages 发布。workflow 先跑 `build_data.py --check`，
再用 `build_site.py` 组装 `_site`（`index.html` 注入两个数据文件的 `?v=<UTC 时间>` 版本号、
44 张品牌页、`sitemap.xml`、`robots.txt`），并断言产物齐全（首页版本号、品牌页数量、
品牌索引已替换、月度序列月份数），任何一条不通过就中止发布。原始调研 JSON 与采集脚本不会随站点公开。

## 访问统计后端（可选）

前端目前 `STATS_API = ""`，不接入时计数区块不显示——纯静态站点本来也记不了访客。
需要时单独部署 `stats_server.py`：

```bash
pip install -r requirements.txt
ADMIN_TOKEN=$(openssl rand -hex 16) \
ALLOW_ORIGIN=https://moonquake2004.github.io \
PORT=5000 python stats_server.py
```

| 环境变量 | 说明 |
| --- | --- |
| `ADMIN_TOKEN` | 必填。`/admin` 的访问口令，不设就拒绝启动（避免默认口令裸奔） |
| `ALLOW_ORIGIN` | 前端域名。留空则**不输出** CORS 头，浏览器会拦截跨域上报 |
| `STATS_DB` | SQLite 路径，默认 `stats.db` |
| `TRUST_PROXY` | 置 1 表示无条件信任 `X-Forwarded-For`（默认仅在 peer 为内网/本机时信任） |
| `GEO_ENABLE` | 置 0 关闭归属地查询（默认开启，会把访客 IP 以 http 明文发给 ip-api.com） |

接口：

- `POST /api/visit` —— 落库后立即返回，归属地由后台线程补写（同 IP 60s 内只记一条）
- `GET /api/stats` —— `{pv, uv24, uv_all}`
- `GET /admin` —— 访客明细，需 `X-Admin-Token` 头或 `?token=`

前端接入时把 `STATS_API` 改成后端地址，且**必须是 https**，否则会被 mixed-content 拦掉。

## 已知取舍

- 月度序列现在只画「当年 1 月至今」，不是因为懒：商会 2025 年 5/6 月两篇稿的 250cc+ 数字重复，
  且与两篇稿自己写的环比互相矛盾，回溯拼长序列会把原稿错误变成趋势。要用 2025 逐月对照，
  得先找到一条能互证的第三方月度源（券商研报只给季度或累计，目前没找到）。
- 品牌的 `note` 字段保留的是调研过程的原始记录（含"官网返回 403"这类工作日志），
  前端直接展示，后续可考虑收进折叠的"数据依据"。
