import networkx as nx
from s2 import find_obvious_cuts


def test_find_obvious_cuts_simple():
    G = nx.Graph()
    G.add_node(0, label=-1)
    G.add_node(1, label=+1)
    G.add_edge(0, 1)
    assert find_obvious_cuts(G) == [(0, 1)]

    G.add_node(2, label=+1)
    G.add_edge(0, 2)
    assert find_obvious_cuts(G) == [(0, 1), (0, 2)]

    G.add_edge(1, 2)
    assert find_obvious_cuts(G) == [(0, 1), (0, 2)]