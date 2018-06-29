from collections import deque
import networkx as nx

def moss(G, U, V):
    queue_u,   queue_v = deque([]), deque([])
    visited_u, visited_v = set(), set()

    for u in U:
        queue_u.append((u, G.neighbors(u)))
        visited_u.add(u)

    for v in V:
        queue_v.append((v, G.neighbors(v)))
        visited_v.add(v)

    while queue_u and queue_v:
        parent, children = queue_u.popleft()
        for child in children:
            if child not in visited_u:
                visited_u.add(child)
                queue_u.append((child, G.neighbors(child)))
                if child in visited_v and child not in V:
                    return child

        parent, children = queue_v.popleft()
        for child in children:
            if child not in visited_v:
                visited_v.add(child)
                queue_v.append((child, G.neighbors(child)))
                if child in visited_u and child not in U:
                    return child
