from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def quote_route(edges: list[tuple[str, str, str]], start: str, end: str, rules: list[dict]) -> dict:
    """edges 为 (a, b, line_code) 三元组。回包含途经边序列与换线次数。

    线路快照在询价当刻写入 result_json；日后改色带不会回填历史记录。
    """
    path = shortest_path(edges, start, end)
    if path is None:
        return {
            "start": start,
            "end": end,
            "hops": None,
            "fare": None,
            "reachable": False,
            "path_edges": [],
            "line_sequence": [],
            "transfers": 0,
        }
    hops = len(path)
    fare = fare_for_hops(hops, rules)
    path_edges = [{"a": a, "b": b, "line_code": lc} for a, b, lc in path]
    line_sequence = [e["line_code"] for e in path_edges]
    transfers = sum(
        1 for i in range(1, len(line_sequence)) if line_sequence[i] != line_sequence[i - 1]
    )
    return {
        "start": start,
        "end": end,
        "hops": hops,
        "fare": fare,
        "reachable": True,
        "path_edges": path_edges,
        "line_sequence": line_sequence,
        "transfers": transfers,
    }
