import sqlite3
from collections import defaultdict


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT code, name, color FROM lines ORDER BY code").fetchall()
    return [dict(r) for r in rows]


def get(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute(
        "SELECT code, name, color FROM lines WHERE code=?", (code,)
    ).fetchone()
    return dict(row) if row else None


def codes_set(conn: sqlite3.Connection) -> set[str]:
    return {r["code"] for r in conn.execute("SELECT code FROM lines").fetchall()}


def update_color(conn: sqlite3.Connection, code: str, color: str) -> bool:
    cur = conn.execute("UPDATE lines SET color=? WHERE code=?", (color, code))
    return cur.rowcount > 0


def station_lines_map(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """站点编码 -> 归属线路列表（编码/显示名/色带），按线路编码排序。"""
    rows = conn.execute(
        """
        SELECT sl.station_code AS station_code, l.code AS code, l.name AS name, l.color AS color
        FROM station_lines sl JOIN lines l ON l.code = sl.line_code
        ORDER BY sl.station_code, l.code
        """
    ).fetchall()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        grouped[r["station_code"]].append({"code": r["code"], "name": r["name"], "color": r["color"]})
    return grouped


def replace_station_lines(conn: sqlite3.Connection, station_code: str, line_codes: list[str]) -> None:
    """整体替换站点归属；调用方须先校验站点与线路均存在、列表非空。"""
    conn.execute("DELETE FROM station_lines WHERE station_code=?", (station_code,))
    conn.executemany(
        "INSERT INTO station_lines(station_code, line_code) VALUES (?,?)",
        [(station_code, lc) for lc in line_codes],
    )
