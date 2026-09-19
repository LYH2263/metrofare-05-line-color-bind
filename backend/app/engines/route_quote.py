from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def _lookup_line(edge_lines: dict, a: str, b: str) -> str | None:
    """边按无向处理：两种方向都查得到。"""
    if (a, b) in edge_lines:
        return edge_lines[(a, b)]
    return edge_lines.get((b, a))


def quote_route(
    edges: list[tuple],
    start: str,
    end: str,
    rules: list[dict],
    edge_lines: dict[tuple[str, str], str | None] | None = None,
    lines: dict[str, dict] | None = None,
) -> dict:
    """最短站数询价。

    有边线路数据时，回包额外给出：
    - path: 途经站点编码序列
    - line_sequence: 途经每条边所属线路的快照序列（编码/显示名/色带）
    - transfers: 换线次数，相邻两边线路不同即一次
    """
    edge_lines = edge_lines or {}
    lines = lines or {}
    path = shortest_path(edges, start, end)
    if path is None:
        return {"start": start, "end": end, "hops": None, "fare": None, "reachable": False}
    hops = len(path) - 1
    fare = fare_for_hops(hops, rules)
    result = {"start": start, "end": end, "hops": hops, "fare": fare, "reachable": True}

    line_codes: list[str | None] = []
    for a, b in zip(path, path[1:]):
        line_codes.append(_lookup_line(edge_lines, a, b))
    transfers = sum(
        1 for prev, cur in zip(line_codes, line_codes[1:]) if prev != cur
    )
    line_sequence = [
        {"code": code, **({"name": lines[code]["name"], "color": lines[code]["color"]}
                          if code in lines else {"name": None, "color": None})}
        for code in line_codes
    ]
    result.update(
        path=path, line_sequence=line_sequence, transfers=transfers
    )
    return result
