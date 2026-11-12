# 国内 250cc+ 摩托车品牌看板

一个纯静态的摩托车市场看板：44 个品牌、424 款 ≥250cc 在售车型（另有 14 款平行进口单独标注、不计入统计口径），按圈层 / 排量段 / 车型类别 / 价格区间交叉筛选，可多词搜索、按价格或排量排序，附品牌墙、市场大盘、图表联动与数据口径说明。

界面为深色工业风，支持浅色主题切换、品牌收藏（存 localStorage）、品牌详情右侧抽屉；排量 / 类别 / 圈层三张条形图点击即筛到型号浏览器。价格六档按**起售价**落档，六档相加正好等于 438（含平行进口）。

线上站点：<https://moonquake2004.github.io/moto-dashboard/>

## 目录结构

```
index.html              单页站点（样式与逻辑内联）
build_data.py           数据构建 + 校验：data/brands_*.json → data/dashboard.js / dashboard.json
data/brands_a~d.json    人工维护的原始数据（唯一的事实来源，改数据只改这里）
data/dashboard.js       构建产物，前端直接加载（window.MOTO_DATA）
data/dashboard.json     构建产物，同内容，供人/脚本查看
data/logos.json         Logo 获取情况清单
assets/logos/           本地化的品牌官方 Logo
assets/favicon.svg      站点图标
assets/publish_api.py   备用发布通道（github.com 不可达时走 api.github.com）
stats_server.py         可选：访问统计后端（Flask + SQLite）
scripts/                一次性数据整理脚本（历史存档，正常不用再跑）
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

## 部署

推送到 `main` 即触发 GitHub Pages 发布。workflow 只发布 `index.html`、`data/dashboard.js`、
`assets/logos/`、`assets/favicon.svg`、`.nojekyll`；原始调研 JSON 与采集脚本不会随站点公开。
发布前会先跑 `build_data.py --check`，数据不合法就构建失败。数据文件请求会带上 `?v=<UTC 时间>`
版本号，避免 Pages 的 10 分钟缓存导致更新延迟。

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

- `index.html` 里有两套设计系统叠着（含一个占 CSS 约 43% 的 RACE DAY 覆盖层），
  合并需要逐屏视觉回归，暂未动。
- 品牌的 `note` 字段保留的是调研过程的原始记录（含"官网返回 403"这类工作日志），
  前端直接展示，后续可考虑收进折叠的"数据依据"。
