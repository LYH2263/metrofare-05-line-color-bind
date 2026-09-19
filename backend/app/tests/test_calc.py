from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops, shortest_path
from app.engines.route_quote import quote_route

EDGES = [
    ("A1", "A2", "A"),
    ("A2", "A3", "A"),
    ("A2", "B1", "B"),
    ("B1", "B2", "B"),
]
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


def test_shortest_path_carries_edges():
    path = shortest_path(EDGES, "A1", "B2")
    assert [(a, b) for a, b, _ in path] == [("A1", "A2"), ("A2", "B1"), ("B1", "B2")]


def test_line_sequence_and_transfers():
    # A1 -> B2 在 A2 由 A 换入 B：相邻两边线路不同即一次换线
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["line_sequence"] == ["A", "B", "B"]
    assert q["transfers"] == 1


def test_same_line_no_transfer():
    q = quote_route(EDGES, "A1", "A3", RULES)
    assert q["line_sequence"] == ["A", "A"]
    assert q["transfers"] == 0


def test_unreachable_shape():
    q = quote_route(EDGES, "A1", "ZZ", RULES)
    assert q["reachable"] is False
    assert q["line_sequence"] == [] and q["transfers"] == 0
