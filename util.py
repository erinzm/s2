import networkx as nx

def draw_labeled_graph(G, oracle):
    def label_to_color(l):
        if l is None: return '0.75'
        return 'r' if l > 0 else 'b'

    nx.draw(G,
        pos={n: n for n in G.nodes()},
        node_color=[label_to_color(oracle(n)) for n in G.nodes()])
