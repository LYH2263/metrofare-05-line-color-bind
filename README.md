# 13-metrofare（地铁票价）

Metrofare — 站间最短站数 + 分段票价表

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4200 |
| API | http://localhost:9200 |

## 主链

选起终点站 → 按站数/里程规则算票价 → 出示票价卡（含途经边线路序列与换线次数）

## 线路色带

- 线路维护编码、显示名、色带（`#RRGGBB`）；站点至少归属一条线路，边标明所属线路。
- `PATCH /api/lines/{code}` 改色带/显示名：非法色值 400，线路不存在 404。
- `PUT /api/stations/{code}/lines` 整单替换站点归属：含不存在线路或为空时 400 且事务回滚，不留半截归属。
- 线网概览、站点详情、邻接列表均带线路编码与色带；改色后同一口径。
- 询价回包 `line_sequence` 为途经边线路序列，相邻两边线路不同计一次换线（`transfers`）。
- 色带随询价结果快照写入历史，之后改色不回填；起终点编码也永不改写。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
