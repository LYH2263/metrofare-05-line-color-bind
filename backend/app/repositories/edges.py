import sqlite3


def list_rows(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute("SELECT a, b, line_code FROM edges ORDER BY line_code, a, b").fetchall()
    ]


def list_pairs(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    return [(r["a"], r["b"], r["line_code"]) for r in conn.execute("SELECT a, b, line_code FROM edges").fetchall()]
