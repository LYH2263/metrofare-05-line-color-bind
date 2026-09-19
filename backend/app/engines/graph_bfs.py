from collections import defaultdict, deque


def _build_graph(edges: list[tuple]) -> dict[str, list[tuple[str, tuple]]]:
    """邻接表：node -> [(邻居, 原始边), ...]，保留边三元组上的线路编码。"""
    g: dict[str, list[tuple[str, tuple]]] = defaultdict(list)
    for e in edges:
        a, b = e[0], e[1]
        g[a].append((b, e))
        g[b].append((a, e))
    return g


def shortest_hops(edges: list[tuple[str, str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count; None if unreachable."""
    path = shortest_path(edges, start, end)
    return None if path is None else len(path)


def shortest_path(edges: list[tuple], start: str, end: str) -> list[tuple] | None:
    """BFS 最短路径，返回途经边（原始三元组 (a,b,line_code)）；不可达返回 None。"""
    if start == end:
        return []
    g = _build_graph(edges)
    if start not in g or end not in g:
        return None
    parents: dict[str, tuple[str, tuple]] = {}
    q = deque([start])
    seen = {start}
    while q:
        cur = q.popleft()
        for nxt, edge in g[cur]:
            if nxt in seen:
                continue
            seen.add(nxt)
            parents[nxt] = (cur, edge)
            if nxt == end:
                q.clear()
                break
            q.append(nxt)
    if end not in parents:
        return None
    path: list[tuple] = []
    node = end
    while node != start:
        prev, edge = parents[node]
        path.append(edge)
        node = prev
    path.reverse()
    return path
