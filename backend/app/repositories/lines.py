import re
import sqlite3

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,16}$")


class ValidationError(ValueError):
    """请求体非法（色值/编码/空归属等），映射为 400。"""


def validate_color(color: str) -> str:
    if not isinstance(color, str) or not COLOR_RE.match(color.strip()):
        raise ValidationError("色值必须为 #RRGGBB 六位十六进制")
    return color.strip().upper()


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT code, name, color FROM lines ORDER BY code").fetchall()]


def get_map(conn: sqlite3.Connection) -> dict[str, dict]:
    return {r["code"]: dict(r) for r in conn.execute("SELECT code, name, color FROM lines").fetchall()}


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT code, name, color FROM lines WHERE code=?", (code,)).fetchone()
    return dict(row) if row else None


def station_line_codes(conn: sqlite3.Connection, station_code: str) -> list[str]:
    return [
        r["line_code"]
        for r in conn.execute(
            "SELECT line_code FROM station_lines WHERE station_code=? ORDER BY line_code",
            (station_code,),
        ).fetchall()
    ]


def all_station_memberships(conn: sqlite3.Connection) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in conn.execute(
        "SELECT station_code, line_code FROM station_lines ORDER BY station_code, line_code"
    ).fetchall():
        out.setdefault(r["station_code"], []).append(r["line_code"])
    return out


def replace_station_lines(conn: sqlite3.Connection, station_code: str, line_codes: list[str]) -> list[str]:
    """整单替换站点归属：任一线路不存在或归属为空即整体回滚，绝不留半截归属。"""
    if not line_codes:
        raise ValidationError("站点至少归属一条线路")
    cleaned: list[str] = []
    for lc in line_codes:
        if not isinstance(lc, str) or not CODE_RE.match(lc.strip()):
            raise ValidationError(f"非法线路编码: {lc!r}")
        lc = lc.strip()
        if lc not in cleaned:
            cleaned.append(lc)
    try:
        conn.execute("BEGIN")
    except sqlite3.OperationalError:
        # 已在事务中（测试或上层调用），沿用当前事务
        pass
    try:
        if conn.execute("SELECT 1 FROM stations WHERE code=?", (station_code,)).fetchone() is None:
            raise ValidationError(f"站点不存在: {station_code}")
        placeholders = ",".join("?" for _ in cleaned)
        found = {
            r["code"]
            for r in conn.execute(
                f"SELECT code FROM lines WHERE code IN ({placeholders})", cleaned
            ).fetchall()
        }
        missing = [lc for lc in cleaned if lc not in found]
        if missing:
            raise ValidationError(f"线路不存在: {', '.join(missing)}")
        conn.execute("DELETE FROM station_lines WHERE station_code=?", (station_code,))
        conn.executemany(
            "INSERT INTO station_lines(station_code, line_code) VALUES (?,?)",
            [(station_code, lc) for lc in cleaned],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return cleaned
