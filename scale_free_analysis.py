import analysis
import pandas as pd
import numpy as np
from config import processed_path
import matplotlib.pyplot as plt
import database
import networkx as nx
import analysis

def degree_distribution_graph(embryo_ID):
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

    metadata_df = database.initialise_metadata()
    stage = metadata_df.loc[embryo_ID,"Stage"]
    n = metadata_df.loc[embryo_ID,"Stage"]
    
    plt.plot(range(k_max+1),degree_dist,label=f"n={n}")
    plt.xlabel("k")
    plt.ylabel("P(k)")
    #plt.legend()

    plt.title(f"Degree distribution of a HH{int(stage)} Embryo")



def clustering_graph(embryo_ID):
    nodes_path = processed_path / "skeleton_networks"
    nodes = pd.read_csv(nodes_path / f"{embryo_ID}_nodes.csv", index_col = 0)
    adj = pd.read_csv(nodes_path / f"{embryo_ID}_adj.csv", index_col = 0)
    adj.columns = adj.columns.astype(int)
    

    G = analysis.gen_networkx_graph(nodes,adj)
    nodes["clustering"] = nx.clustering(G)
    
    plt.hist(nodes["clustering"],bins=50)

    plt.xlabel("Clustering Coefficient")
    plt.ylabel("Total Nodes")

    metadata_df = database.initialise_metadata()
    stage = metadata_df.loc[embryo_ID,"Stage"]
    plt.title(f"Clustering Coefficient Distribution of a HH{int(stage)} Embryo")



