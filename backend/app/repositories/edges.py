import sqlite3


def list_rows(conn: sqlite3.Connection) -> list[dict]:
    """返回区间及其所属线路（编码/显示名/色带），按 a、b 排序。"""
    rows = conn.execute(
        """
        SELECT e.a AS a, e.b AS b,
               l.code AS line_code, l.name AS line_name, l.color AS line_color
        FROM edges e LEFT JOIN lines l ON l.code = e.line_code
        ORDER BY e.a, e.b
        """
    ).fetchall()
    return [dict(r) for r in rows]


def list_pairs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    return [(r["a"], r["b"]) for r in conn.execute("SELECT a,b FROM edges").fetchall()]


def edge_line_map(conn: sqlite3.Connection) -> dict[tuple[str, str], str | None]:
    return {(r["a"], r["b"]): r["line_code"] for r in
            conn.execute("SELECT a, b, line_code FROM edges").fetchall()}
