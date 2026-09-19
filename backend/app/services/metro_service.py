import re

from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import lines as lines_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class ValidationError(Exception):
    """请求体语义非法（区别于 404 的资源不存在）。"""


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return edges_repo.list_rows(self._conn)

    def lines(self):
        return lines_repo.list_all(self._conn)

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def update_line_color(self, code: str, color: str) -> dict:
        if not COLOR_RE.match(color or ""):
            raise ValidationError(f"非法色值: {color!r}，需为 #RRGGBB 形式")
        if not lines_repo.get(self._conn, code):
            return None
        lines_repo.update_color(self._conn, code, color)
        self._conn.commit()
        return lines_repo.get(self._conn, code)

    def update_station_lines(self, code: str, line_codes: list[str]) -> dict:
        if not stations_repo.exists(self._conn, code):
            return None
        # 去重但保序；空归属非法（站点至少归属一条线路）
        deduped = list(dict.fromkeys(line_codes or []))
        if not deduped:
            raise ValidationError("站点至少归属一条线路")
        known = lines_repo.codes_set(self._conn)
        missing = [lc for lc in deduped if lc not in known]
        if missing:
            raise ValidationError(f"线路不存在: {', '.join(missing)}")
        try:
            # 单事务整体替换：任何失败都回滚，不留半截归属
            with self._conn:
                lines_repo.replace_station_lines(self._conn, code, deduped)
        except Exception:
            self._conn.rollback()
            raise
        return stations_repo.get_by_code(self._conn, code)

    def quote(self, start: str, end: str, persist: bool):
        pairs = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        edge_lines = edges_repo.edge_line_map(self._conn)
        line_rows = {l["code"]: l for l in lines_repo.list_all(self._conn)}
        result = quote_route(
            pairs, start, end, rules, edge_lines=edge_lines, lines=line_rows
        )
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        grouped: dict[str, list[dict]] = {}
        for s in st:
            for line in s["lines"]:
                grouped.setdefault(line["code"], []).append(
                    {"code": s["code"], "name": s["name"]}
                )
        lines = []
        for line in lines_repo.list_all(self._conn):
            lines.append({**line, "stations": grouped.get(line["code"], [])})
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
            "lines": lines,
        }
