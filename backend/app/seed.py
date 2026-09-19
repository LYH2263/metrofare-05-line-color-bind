import json

from app.db import connect
from app.engines.route_quote import quote_route

# 种子区间：a, b, 所属线路编码
SEED_EDGES = [
    ("A1", "A2", "L1"),
    ("A2", "A3", "L1"),
    ("A2", "B1", "L2"),
    ("B1", "B2", "L2"),
]
# 站点归属：站点编码 -> 线路编码集合（A2 为两线换乘站）
SEED_STATION_LINES = {
    "A1": ["L1"],
    "A2": ["L1", "L2"],
    "A3": ["L1"],
    "B1": ["L2"],
    "B2": ["L2"],
}
SEED_LINES = [
    ("L1", "1号线", "#e85d04"),
    ("L2", "支线", "#2a9d8f"),
]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


def _migrate_edges_column(conn) -> None:
    """旧库 edges 没有 line_code 时补列（DDL 自动提交，列存在后由幂等补齐回填值）。"""
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(edges)").fetchall()]
    if "line_code" not in cols:
        conn.execute("ALTER TABLE edges ADD COLUMN line_code TEXT")
        conn.commit()


def _migrate_stations_unique(conn) -> None:
    """旧库 stations.code 无唯一约束；外键要求被引用列唯一，需在子表建立前重建。"""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='stations'"
    ).fetchone()
    if row is None:
        # 全新库，stations 稍后按带 UNIQUE 的定义创建
        return
    if "UNIQUE" in row["sql"].upper():
        return
    conn.executescript(
        """
        CREATE TABLE stations_new(id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT);
        INSERT INTO stations_new SELECT id, code, name FROM stations;
        DROP TABLE stations;
        ALTER TABLE stations_new RENAME TO stations;
        """
    )
    conn.commit()


def _ensure_line_data(conn) -> None:
    """对新旧库均幂等：补线路、补缺失归属、回填尚无线路的种子区间，不覆盖用户改动。"""
    for line_code, line_name, color in SEED_LINES:
        conn.execute(
            "INSERT OR IGNORE INTO lines(code, name, color) VALUES (?,?,?)",
            (line_code, line_name, color),
        )
    for station_code, line_codes in SEED_STATION_LINES.items():
        if not conn.execute(
            "SELECT 1 FROM stations WHERE code=?", (station_code,)
        ).fetchone():
            continue
        for line_code in line_codes:
            conn.execute(
                "INSERT OR IGNORE INTO station_lines(station_code, line_code) VALUES (?,?)",
                (station_code, line_code),
            )
    for a, b, line_code in SEED_EDGES:
        conn.execute(
            "UPDATE edges SET line_code=? WHERE a=? AND b=? AND line_code IS NULL",
            (line_code, a, b),
        )
    conn.commit()


def init_db():
    conn = connect()
    # 旧库站点表需先补上 code 唯一约束，子表外键才能建立
    _migrate_stations_unique(conn)
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS stations(id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT);
    CREATE TABLE IF NOT EXISTS lines(
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        color TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS station_lines(
        station_code TEXT NOT NULL REFERENCES stations(code) ON DELETE CASCADE,
        line_code TEXT NOT NULL REFERENCES lines(code) ON DELETE RESTRICT,
        PRIMARY KEY (station_code, line_code));
    CREATE TABLE IF NOT EXISTS edges(
        a TEXT NOT NULL REFERENCES stations(code),
        b TEXT NOT NULL REFERENCES stations(code),
        line_code TEXT REFERENCES lines(code),
        PRIMARY KEY (a, b));
    CREATE TABLE IF NOT EXISTS fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(
        id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
    """
    )
    _migrate_edges_column(conn)
    _ensure_line_data(conn)

    if conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] == 0:
        for code, name in [
            ("A1", "城站"),
            ("A2", "市心"),
            ("A3", "东湾"),
            ("B1", "北苑"),
            ("B2", "机场(种子绕远)"),
        ]:
            conn.execute("INSERT INTO stations(code, name) VALUES (?,?)", (code, name))
        for a, b, _line_code in SEED_EDGES:
            conn.execute("INSERT INTO edges(a, b) VALUES (?,?)", (a, b))
        conn.executemany(
            "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
            [(2, 3.0), (4, 4.0), (None, 6.0)],
        )
        conn.execute("INSERT INTO settings(key,value) VALUES ('currency','CNY')")
        conn.commit()
        # 再补一次归属/边色带（站点与边此刻才落库）
        _ensure_line_data(conn)
        seed_edges = [(a, b) for a, b, _ in SEED_EDGES]
        edge_lines = {(a, b): lc for a, b, lc in SEED_EDGES}
        line_rows = {code: {"code": code, "name": name, "color": color}
                     for code, name, color in SEED_LINES}
        q1 = quote_route(seed_edges, "A1", "A3", RULES, edge_lines=edge_lines, lines=line_rows)
        conn.execute(
            "INSERT INTO calc_runs(kind,input_json,result_json,created_at) VALUES (?,?,?,datetime('now'))",
            ("quote", json.dumps({"start": "A1", "end": "A3"}), json.dumps(q1, ensure_ascii=False)),
        )
        conn.commit()
    conn.close()
