import json
import os
import tempfile

# 必须在导入 app.* 之前指向独立测试库
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="metrofare-test-"))

from fastapi.testclient import TestClient

from app.main import app
from app import seed

seed.init_db()
client = TestClient(app)


def test_lines_list_band():
    items = client.get("/api/lines").json()["items"]
    by = {x["code"]: x for x in items}
    assert set(by) == {"A", "B"}
    assert by["A"]["color"] == "#E85D04" and by["A"]["name"] == "1号线"


def test_station_detail_carries_lines():
    st = client.get("/api/stations/A2").json()
    assert st["line_codes"] == ["A", "B"]
    assert {l["code"] for l in st["lines"]} == {"A", "B"}
    assert all("color" in l and l["color"].startswith("#") for l in st["lines"])
    # 每个站点至少归属一条线路
    for s in client.get("/api/stations").json()["items"]:
        assert len(s["line_codes"]) >= 1


def test_edges_carry_line_band():
    e = client.get("/api/edges").json()["items"][0]
    assert {"a", "b", "line_code", "line_color", "line_name"} <= set(e)
    ab = {(x["a"], x["b"]): x for x in client.get("/api/edges").json()["items"]}
    assert ab[("A2", "B1")]["line_code"] == "B"


def test_dashboard_groups_by_lines():
    d = client.get("/api/dashboard").json()
    assert {l["code"] for l in d["lines"]} == {"A", "B"}
    a2 = next(s for s in d["stations"] if s["code"] == "A2")
    assert "A" in a2["line_codes"] and "B" in a2["line_codes"]


def test_quote_line_sequence_and_transfers():
    q = client.post("/api/quote", json={"start": "A1", "end": "B2", "persist": False}).json()
    assert q["reachable"]
    assert q["start"] == "A1" and q["end"] == "B2"  # 起终点编码不变
    assert q["line_sequence"] == ["A", "B", "B"]
    assert q["transfers"] == 1
    assert [e["line_color"] for e in q["path_edges"]]  # 每条边带当刻色带
    assert q["path_edges"][0]["line_code"] == "A"


def test_change_band_rejects_bad_color():
    before = next(x for x in client.get("/api/lines").json()["items"] if x["code"] == "A")["color"]
    r = client.patch("/api/lines/A", json={"color": "red"})
    assert r.status_code == 400
    r = client.patch("/api/lines/A", json={"color": "#12"})
    assert r.status_code == 400
    r = client.patch("/api/lines/ZZ", json={"color": "#123456"})
    assert r.status_code == 404
    # 失败后原色带不动
    after = next(x for x in client.get("/api/lines").json()["items"] if x["code"] == "A")
    assert after["color"] == before


def test_change_band_ok_takes_effect_everywhere():
    assert client.patch("/api/lines/A", json={"color": "#112233"}).status_code == 200
    # 线网概览与站点详情同一口径
    dash = next(x for x in client.get("/api/dashboard").json()["lines"] if x["code"] == "A")
    detail = next(l for l in client.get("/api/stations/A1").json()["lines"] if l["code"] == "A")
    edge = next(e for e in client.get("/api/edges").json()["items"] if e["line_code"] == "A")
    assert dash["color"] == detail["color"] == edge["line_color"] == "#112233"
    # 询价当刻取新色带，但起终点编码不变
    q = client.post("/api/quote", json={"start": "A1", "end": "A3", "persist": False}).json()
    assert all(e["line_color"] == "#112233" for e in q["path_edges"])
    assert q["start"] == "A1" and q["end"] == "A3"


def test_change_membership_unknown_line_leaves_no_half_state():
    before = client.get("/api/stations/A1").json()["line_codes"]
    r = client.put("/api/stations/A1/lines", json={"line_codes": ["A", "ZZ"]})
    assert r.status_code == 400
    after = client.get("/api/stations/A1").json()["line_codes"]
    assert after == before  # 失败不留半截归属


def test_change_membership_empty_rejected():
    r = client.put("/api/stations/A1/lines", json={"line_codes": []})
    assert r.status_code == 400
    assert client.get("/api/stations/A1").json()["line_codes"] == ["A"]


def test_change_membership_ok():
    r = client.put("/api/stations/A3/lines", json={"line_codes": ["A", "B"]})
    assert r.status_code == 200
    assert r.json()["line_codes"] == ["A", "B"]
    r2 = client.put("/api/stations/A3/lines", json={"line_codes": ["B"]})
    assert r2.json()["line_codes"] == ["B"]
    client.put("/api/stations/A3/lines", json={"line_codes": ["A"]})  # 还原


def test_history_snapshot_not_backfilled_after_recolor():
    # 先设已知色，固化一条 A 线询价
    client.patch("/api/lines/A", json={"color": "#112233"})
    client.post("/api/quote", json={"start": "A1", "end": "A3", "persist": True})
    client.patch("/api/lines/A", json={"color": "#ABCDEF"})
    rows = client.get("/api/history").json()["items"]
    snap = json.loads(rows[0]["result_json"])
    assert snap["start"] == "A1" and snap["end"] == "A3"  # 起终点编码不变
    assert snap["path_edges"][0]["line_color"] == "#112233"  # 旧色带不回填


def test_old_schema_migration(monkeypatch, tmp_path):
    import sqlite3

    from app import db as db_mod, seed

    p = tmp_path / "old.db"
    c = sqlite3.connect(p)
    c.executescript(
        """
        CREATE TABLE stations(id INTEGER PRIMARY KEY, code TEXT, name TEXT);
        CREATE TABLE edges(a TEXT, b TEXT);
        CREATE TABLE fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
        CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE calc_runs(id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
        """
    )
    c.executemany("INSERT INTO stations(code,name) VALUES (?,?)", [("A1", "城站"), ("B1", "北苑")])
    c.executemany("INSERT INTO edges(a,b) VALUES (?,?)", [("A1", "A2"), ("B1", "B2")])
    c.commit()
    c.close()

    monkeypatch.setattr(db_mod, "DB_PATH", p)
    seed.init_db()

    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    try:
        codes = {r[0] for r in c.execute("SELECT station_code FROM station_lines")}
        assert codes == {"A1", "B1"}  # 每个旧站点至少补上一条归属
        edge_lines = {r["line_code"] for r in c.execute("SELECT line_code FROM edges")}
        assert edge_lines == {"A", "B"}
    finally:
        c.close()
