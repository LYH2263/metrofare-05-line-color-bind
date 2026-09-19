import sqlite3

from app.repositories import lines as lines_repo


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM stations ORDER BY code").fetchall()
    memberships = lines_repo.station_lines_map(conn)
    return [
        {**dict(r), "lines": memberships.get(r["code"], [])}
        for r in rows
    ]


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM stations WHERE code=?", (code,)).fetchone()
    if not row:
        return None
    memberships = lines_repo.station_lines_map(conn)
    return {**dict(row), "lines": memberships.get(code, [])}


def exists(conn: sqlite3.Connection, code: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM stations WHERE code=?", (code,)
    ).fetchone() is not None
