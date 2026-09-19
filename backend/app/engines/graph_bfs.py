from collections import defaultdict, deque


def shortest_hops(edges: list[tuple], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count; None if unreachable. Accepts 2- or 3-tuples."""
    path = shortest_path(edges, start, end)
    if path is None:
        return None
    return len(path) - 1


def shortest_path(edges: list[tuple], start: str, end: str) -> list[str] | None:
    """Undirected graph BFS; returns ordered station codes [start, ..., end], None if unreachable."""
    if start == end:
        return [start]
    g: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        a, b = edge[0], edge[1]
        g[a].add(b)
        g[b].add(a)
    if start not in g or end not in g:
        return None
    parents: dict[str, str | None] = {start: None}
    q = deque([start])
    found = False
    while q and not found:
        cur = q.popleft()
        for nxt in sorted(g[cur]):
            if nxt in parents:
                continue
            parents[nxt] = cur
            if nxt == end:
                found = True
                break
            q.append(nxt)
    if end not in parents:
        return None
    path: list[str] = []
    cur: str | None = end
    while cur is not None:
        path.append(cur)
        cur = parents[cur]
    return path[::-1]
