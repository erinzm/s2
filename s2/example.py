import networkx as nx
import matplotlib.pyplot as plt
from s2 import s2, path_midpoint, enumerate_find_ssp
from moss import moss
from util import draw_labeled_graph
import timeit


def test_simple_lattice():
    G = nx.grid_2d_graph(10, 10)

    def oracle(vert):
        return ((vert[0] < 3) and (vert[1] < 3)) or ((vert[0] > 6) and (vert[1] > 6))

    # enum: 638 ms ± 22.8 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
    # moss: 18.1 ms ± 75.7 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

    G_cut = s2(G, oracle, lambda G, U, V: moss(G, U, V))

    fig = plt.figure()
    fig.add_subplot(121).title.set_text('Ground-truth')
    draw_labeled_graph(G, oracle)

    fig.add_subplot(122).title.set_text('$S^2$')
    draw_labeled_graph(G_cut, lambda v: G_cut.node[v].get('label'))

    plt.show()

if __name__ == '__main__':
    test_simple_lattice()
