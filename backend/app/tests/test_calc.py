from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops, shortest_path
from app.engines.route_quote import quote_route

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
# 与种子一致：A1-A2/A2-A3 在 L1，A2-B1/B1-B2 在 L2
EDGE_LINES = {("A1", "A2"): "L1", ("A2", "A3"): "L1", ("A2", "B1"): "L2", ("B1", "B2"): "L2"}
LINES = {
    "L1": {"code": "L1", "name": "1号线", "color": "#e85d04"},
    "L2": {"code": "L2", "name": "支线", "color": "#2a9d8f"},
}
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


def test_hops_a1_a3():
    assert shortest_hops(EDGES, "A1", "A3") == 2


def test_hops_a1_b2():
    assert shortest_hops(EDGES, "A1", "B2") == 3


def test_fare_by_hops():
    assert fare_for_hops(2, RULES) == 3.0
    assert fare_for_hops(3, RULES) == 4.0
    assert fare_for_hops(10, RULES) == 6.0


def test_quote():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["hops"] == 3 and q["fare"] == 4.0


def test_shortest_path():
    assert shortest_path(EDGES, "A1", "A3") == ["A1", "A2", "A3"]
    assert shortest_path(EDGES, "A1", "A1") == ["A1"]
    assert shortest_path(EDGES, "A1", "X9") is None


def test_quote_line_sequence_with_transfer():
    q = quote_route(EDGES, "A1", "B2", RULES, edge_lines=EDGE_LINES, lines=LINES)
    assert q["path"] == ["A1", "A2", "B1", "B2"]
    assert [seg["code"] for seg in q["line_sequence"]] == ["L1", "L2", "L2"]
    # 色带随回包带出
    assert q["line_sequence"][0]["color"] == "#e85d04"
    assert q["line_sequence"][0]["name"] == "1号线"
    # 仅 L1->L2 一次换线
    assert q["transfers"] == 1


def test_quote_line_sequence_same_line_no_transfer():
    q = quote_route(EDGES, "A1", "A3", RULES, edge_lines=EDGE_LINES, lines=LINES)
    assert [seg["code"] for seg in q["line_sequence"]] == ["L1", "L1"]
    assert q["transfers"] == 0


def test_quote_accepts_three_tuples():
    triples = [(a, b, lc) for (a, b), lc in EDGE_LINES.items()]
    q = quote_route(triples, "A1", "B2", RULES, edge_lines=EDGE_LINES, lines=LINES)
    assert q["hops"] == 3 and q["transfers"] == 1
