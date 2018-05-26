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
import numpy as np
import random


def s2(G, oracle):
    """
    Runs the S² algorithm on a graph, returning the cut set.

    Parameters
    ----------
    G : nx.Graph
        The input graph to the algorithm.
    oracle : fn(vertex) -> bool
        An oracle function, taking a vertex and returning the label as a `bool`.
    """
    G = G.copy()

    # number of vertices
    n = G.order()

    # labeled set. represented as a list of (vert, label) pairs.
    L = []

    while True:
        # pick a random point and query it
        rand_vertex = random.choice(G.nodes())
        y = oracle(rand_vert)
        # add it to the labelled set
        L.append((rand_vert, y))
        # mark it as labelled
        G.node[rand_vert]['label'] = y

        while True:
            # find obvious cuts
            cuts = find_obvious_cuts(G)
            # unzip
            G.remove_edges_from(cuts)



def find_obvious_cuts(G):
    """
    Find obvious cuts between adjacent verts of different labels.

    Parameters
    ----------
    G : nx.Graph
        The input graph, with nodes with known label marked with the data attribute `label`.
    """
    
    cuts = []

    labeled_nodes = [v[0] for v in G.nodes_iter(data=True) if v[1].get('label') is not None]

    labeled_subgraph = G.subgraph(labeled_nodes)
    for edge in labeled_subgraph.edges_iter():
        if G.node[edge[0]]['label'] != G.node[edge[1]]['label']:
            cuts.append(edge)

    return cuts