import analysis
import pandas as pd
import numpy as np
from config import processed_path
import matplotlib.pyplot as plt
import database

def scale_free_graph(embryo_ID):
    nodes_path = processed_path / "skeleton_networks"
    nodes = pd.read_csv(nodes_path / f"{embryo_ID}_nodes.csv", index_col = 0)
    adj = pd.read_csv(nodes_path / f"{embryo_ID}_adj.csv", index_col = 0)
    adj.columns = adj.columns.astype(int)

    nodes = analysis.calc_degrees(nodes,adj)

    N=len(nodes)
    k_max = int(nodes["degree"].max())
    degree_dist = []
    for i in range(k_max+1):
        degree_dist.append(len(nodes[nodes["degree"]==i])/N)

    plt.plot(range(k_max+1),degree_dist)
    plt.xlabel("k")
    plt.ylabel("P(k)")


