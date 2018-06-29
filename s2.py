"""
Implements S², an Efficient Graph-Based Active Learning Algorithm.

@inproceedings{dasarathy2015s2,
  title={S2: An efficient graph based active learning algorithm with application to nonparametric classification},
  author={Dasarathy, Gautam and Nowak, Robert and Zhu, Xiaojin},
  booktitle={Conference on Learning Theory},
  pages={503--522},
  year={2015}
}
"""

import networkx as nx
import random
import itertools


def s2(G, oracle, find_moss):
    """
    Runs the S² algorithm on a graph, returning the unzipped graph.

    Parameters
    ----------
    G : nx.Graph
        The input graph to the algorithm.
    oracle : fn(vertex) -> bool
        An oracle function, taking a vertex and returning the label as a `bool`.
    find_moss : fn(G : nx.Graph, U : [vertex], V : [vertex]) -> list of vertices or `None`
        A function which, given a graph and two sets of vertices, returns the Midpoint Of the Shortest Shortest path
        between any pair of vertices across these two sets.
    """
    G = G.copy()

    # number of vertices
    n = G.order()

    # labeled sets. U is positively labeled vertices, V is negatively labeled.
    U = set()
    V = set()

    while True:
        if len(U) + len(V) == n:
            break

        # pick a random vertex that we haven't seen before
        vert = random.choice(list(G.nodes()))
        if vert in U or vert in V:
            continue

        while True:
            # query the current vertex
            y = oracle(vert)
            # add the current vertex to one of the labeled sets
            {True: U, False: V}[y].add(vert)
            # mark it as labeled
            G.node[vert]['label'] = y


            # find obvious cuts
            cuts = find_obvious_cuts(G, [(i, True) for i in U] + [(i, False) for i in V])
            # unzip
            G.remove_edges_from(cuts)

            # try to pick a new vertex via midpoint of shortest shortest path
            vert = find_moss(G, U, V)

            # if it's bad, break out of the inner loop and get a new random vert
            if vert is None:
                break

    return G

def find_obvious_cuts(G, L=None):
    """
    Find obvious cuts between adjacent verts of different labels.

    Parameters
    ----------
    G : nx.Graph
        The input graph, with nodes with known label marked with the data attribute `label`.
    L : optional list of (vert, label)
        A list of tuples of vertices with known labels, and their corresponding label.

        Is only used to accelerate slightly so we don't have to re-search the graph; if None,
        we do our own search for `label`s.
    """
    
    if L is None:
        labeled_nodes = [v[0] for v in G.nodes(data=True) if v[1].get('label') is not None]
    else:
        labeled_nodes = [l[0] for l in L]

    labeled_subgraph = G.subgraph(labeled_nodes)

    cuts = []
    # for every pair of labeled vertices
    for edge in labeled_subgraph.edges():
        # for every cut pair of labels
        if G.node[edge[0]]['label'] != G.node[edge[1]]['label']:
            cuts.append(edge)

    return cuts

def path_midpoint(path):
    if path is None:
        return None

    return path[len(path)//2]

def enumerate_find_ssp(G, U, V):
    """
    Finds all shortest paths between pairs of vertices spanning U and V, and returns the shortest one.

    Time complexity is something like
        O(|U|*|V| * n log n) ≈ O((n/2)^2 * n log n) = O(n^3 log n)
    where n = |U| + |V|.

    Probably don't use this, _especially_ if you have a lattice graph.
    """

    paths = []

    # for every pair of labeled vertices
    for (u, v) in itertools.product(U, V):
        try:
            P = nx.shortest_path(G, u, v)
        except nx.NetworkXNoPath:
            # we don't have a path, so skip adding it to the list
            continue

        paths.append(P)

    # if we found no paths, return None
    if paths == []:
        return None

    # find the shortest shortest path
    ssp = min(paths, key=lambda path: len(path))

    return ssp
