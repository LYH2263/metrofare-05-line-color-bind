import sqlite3

from app.repositories import lines as lines_repo


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = [dict(r) for r in conn.execute("SELECT * FROM stations ORDER BY code").fetchall()]
    memberships = lines_repo.all_station_memberships(conn)
    line_map = lines_repo.get_map(conn)
    return [_attach_lines(s, memberships, line_map) for s in rows]


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM stations WHERE code=?", (code,)).fetchone()
    if not row:
        return None
    station = dict(row)
    line_map = lines_repo.get_map(conn)
    memberships = {station["code"]: lines_repo.station_line_codes(conn, station["code"])}
    return _attach_lines(station, memberships, line_map)


def _attach_lines(
    station: dict, memberships: dict[str, list[str]], line_map: dict[str, dict]
) -> dict:
    codes = memberships.get(station["code"], [])
    station["line_codes"] = codes
    station["lines"] = [
        {"code": c, "name": line_map[c]["name"], "color": line_map[c]["color"]}
        for c in codes
        if c in line_map
    ]
    return station
