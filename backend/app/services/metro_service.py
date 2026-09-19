from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import lines as lines_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # ---- 线路 ----
    def lines(self):
        return lines_repo.list_all(self._conn)

    def update_line_band(self, code: str, color: str | None = None, name: str | None = None):
        if color is not None:
            color = lines_repo.validate_color(color)
        existing = lines_repo.get_by_code(self._conn, code)
        if not existing:
            return None
        new_color = color if color is not None else existing["color"]
        new_name = name if name is not None else existing["name"]
        self._conn.execute(
            "UPDATE lines SET color=?, name=? WHERE code=?", (new_color, new_name, code)
        )
        self._conn.commit()
        return lines_repo.get_by_code(self._conn, code)

    def update_station_lines(self, station_code: str, line_codes: list[str]):
        # 站点 404 与线路校验均在仓储的同一事务里完成，失败回滚不留半截归属
        station = stations_repo.get_by_code(self._conn, station_code)
        if not station:
            return None
        codes = lines_repo.replace_station_lines(self._conn, station_code, line_codes)
        return stations_repo.get_by_code(self._conn, station_code)

    # ---- 站点 / 边 ----
    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        line_map = lines_repo.get_map(self._conn)
        out = []
        for e in edges_repo.list_rows(self._conn):
            info = line_map.get(e["line_code"])
            e["line_name"] = info["name"] if info else None
            e["line_color"] = info["color"] if info else None
            out.append(e)
        return out

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        result = quote_route(edges, start, end, rules)
        # 色带在询价当刻随结果固化：日后改色不回填历史
        line_map = lines_repo.get_map(self._conn)
        for pe in result.get("path_edges", []):
            info = line_map.get(pe["line_code"])
            pe["line_name"] = info["name"] if info else None
            pe["line_color"] = info["color"] if info else None
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
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_rows(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
            "lines": lines_repo.list_all(self._conn),
            "stations": st,
        }
