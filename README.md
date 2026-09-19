# 13-metrofare（地铁票价）

Metrofare — 站间最短站数 + 分段票价表，线路色带绑定

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4200 |
| API | http://localhost:9200 |

## 主链

选起终点站 → 按站数/里程规则算票价 → 出示票价卡（含途经线路序列与换线次数）

## 线路色带

- 线路维护编码、显示名、色带（`#RRGGBB`）；站点至少归属一条线路，区间（边）标明所属线路。
- `GET /api/lines`：线路列表（编码/显示名/色带）。
- `PUT /api/lines/{code}/color`：改色带，非法色值返回 422，线路不存在返回 404。
- `PUT /api/stations/{code}/lines`：整体替换站点归属；空归属或含不存在线路返回 422，
  事务提交，失败不留半截归属。
- `GET /api/dashboard`：线网概览，按线路分组并带编码与色带。
- `GET /api/stations/{code}`：站点详情，含归属线路（编码/显示名/色带）。
- `GET /api/edges`：邻接区间，每条边带 `line_code/line_name/line_color`。
- `POST /api/quote`：回包含 `path`、`line_sequence`（途经边线路快照）、`transfers`
  （相邻两边线路不同即一次换线）。
- 已写入的询价记录保存当时色带与起终点编码快照，后续改色不回填。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
