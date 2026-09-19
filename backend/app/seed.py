import json

from app.db import connect
from app.engines.route_quote import quote_route

# (a, b, line_code)
EDGES = [
    ("A1", "A2", "A"),
    ("A2", "A3", "A"),
    ("A2", "B1", "B"),
    ("B1", "B2", "B"),
]
# code, display_name, color
LINES = [("A", "1号线", "#E85D04"), ("B", "支线", "#2A9D8F")]
STATIONS = [
    ("A1", "城站"),
    ("A2", "市心"),
    ("A3", "东湾"),
    ("B1", "北苑"),
    ("B2", "机场(种子绕远)"),
]
# station_code -> 归属线路（换乘站可属多条；市心 A2 为 A/B 换乘站）
STATION_LINES = [
    ("A1", "A"),
    ("A2", "A"),
    ("A2", "B"),
    ("A3", "A"),
    ("B1", "B"),
    ("B2", "B"),
]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


def init_db():
    conn = connect()
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS stations(id INTEGER PRIMARY KEY, code TEXT, name TEXT);
    CREATE TABLE IF NOT EXISTS edges(a TEXT, b TEXT, line_code TEXT);
    CREATE TABLE IF NOT EXISTS lines(code TEXT PRIMARY KEY, name TEXT, color TEXT);
    CREATE TABLE IF NOT EXISTS station_lines(station_code TEXT, line_code TEXT,
        PRIMARY KEY(station_code, line_code));
    CREATE TABLE IF NOT EXISTS fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(
        id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, created_at TEXT, result_json TEXT);
    """
    )
    _migrate_old_schema(conn)
    if conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] == 0:
        conn.executemany("INSERT INTO stations(code, name) VALUES (?,?)", STATIONS)
        for code, name, color in LINES:
            conn.execute("INSERT INTO lines(code, name, color) VALUES (?,?,?)", (code, name, color))
        conn.executemany(
            "INSERT INTO station_lines(station_code, line_code) VALUES (?,?)", STATION_LINES
        )
        conn.executemany("INSERT INTO edges(a,b,line_code) VALUES (?,?,?)", EDGES)
        conn.executemany(
            "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
            [(2, 3.0), (4, 4.0), (None, 6.0)],
        )
        conn.execute("INSERT INTO settings(key,value) VALUES ('currency','CNY')")
        q1 = quote_route(EDGES, "A1", "A3", RULES)
        conn.execute(
            "INSERT INTO calc_runs(kind,input_json,result_json,created_at) VALUES (?,?,?,datetime('now'))",
            ("quote", json.dumps({"start": "A1", "end": "A3"}), json.dumps(q1, ensure_ascii=False)),
        )
        conn.commit()
    conn.close()


def _migrate_old_schema(conn):
    """升级旧库：edges 补 line_code，station_lines 按邻接边回填。已写入的询价快照不动。"""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(edges)").fetchall()]
    if "line_code" not in cols:
        conn.execute("ALTER TABLE edges ADD COLUMN line_code")
        # 旧种子图里 A* 之间属 A 线，其余按 B 线；真实数据交管理员在邻接页校正
        for (a, b) in conn.execute("SELECT a, b FROM edges").fetchall():
            guessed = "A" if str(a).startswith("A") and str(b).startswith("A") else "B"
            conn.execute("UPDATE edges SET line_code=? WHERE a=? AND b=?", (guessed, a, b))
    # 旧库新建出来的 lines 是空表：按边上出现过的编码补默认显示名与色带
    if conn.execute("SELECT COUNT(*) c FROM lines").fetchone()["c"] == 0:
        used = [
            r["line_code"]
            for r in conn.execute("SELECT DISTINCT line_code FROM edges WHERE line_code IS NOT NULL").fetchall()
        ]
        for lc in used:
            conn.execute(
                "INSERT OR IGNORE INTO lines(code, name, color) VALUES (?,?,?)",
                (lc, f"线路{lc}", "#888888"),
            )
    stations_exist = conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] > 0
    memberships_empty = conn.execute("SELECT COUNT(*) c FROM station_lines").fetchone()["c"] == 0
    if stations_exist and memberships_empty:
        for (code,) in conn.execute("SELECT code FROM stations").fetchall():
            line_codes = [
                r["line_code"]
                for r in conn.execute(
                    "SELECT DISTINCT line_code FROM edges "
                    "WHERE line_code IS NOT NULL AND (a=? OR b=?)",
                    (code, code),
                ).fetchall()
            ]
            if not line_codes:
                line_codes = [r["code"] for r in conn.execute("SELECT code FROM lines LIMIT 1").fetchall()]
            for lc in line_codes:
                conn.execute(
                    "INSERT OR IGNORE INTO station_lines(station_code, line_code) VALUES (?,?)",
                    (code, lc),
                )
    conn.commit()
