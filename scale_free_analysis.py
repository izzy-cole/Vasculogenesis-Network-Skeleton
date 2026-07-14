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
    n = metadata_df.loc[embryo_ID,"n"]
    
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
    nodes = analysis.calc_degrees(nodes,adj)
    
    plt.hist(nodes["clustering"],bins=50)

    plt.xlabel("Clustering Coefficient")
    plt.ylabel("Total Nodes")

    metadata_df = database.initialise_metadata()
    stage = metadata_df.loc[embryo_ID,"Stage"]
    plt.title(f"Clustering Coefficient Distribution of a HH{int(stage)} Embryo")


def edge_length_graph(embryo_ID):
    adj = pd.read_csv(nodes_path / f"{embryo_ID}_adj.csv", index_col = 0)
    adj.columns = adj.columns.astype(int)
    
    edge_weights = adj.values
    edge_weights = edge_weights[~np.isnan(edge_weights)]
    
    percentiles = np.arange(0,100,10)
    edge_percentiles = np.percentile(edge_weights,percentiles)

    plt.bar(percentiles,edge_percentiles,width=5)

    plt.xlabel("Percentile")
    plt.ylabel("Edge Length")

    plt.ylim(bottom=0,top=200)

    metadata_df = database.initialise_metadata()
    stage = metadata_df.loc[embryo_ID,"Stage"]
    plt.title(f"Edge Length Distribution of a HH{int(stage)} Embryo")


#Could store the whole-dataset edge percentiles to improve run time
def edge_whole_percentile_graph(embryo_ID,embryo_ID_list):
    nodes_path = processed_path / "skeleton_networks"

    valid_edges = []
    for i in embryo_ID_list:
        adj = pd.read_csv(nodes_path / f"{i}_adj.csv", index_col = 0)
        adj.columns = adj.columns.astype(int)
    
        edge_weights = adj.values
        edge_weights = edge_weights[~np.isnan(edge_weights)]
        valid_edges.extend(edge_weights)

    percentiles = np.arange(0,100,10)
    edge_percentiles = np.percentile(valid_edges,percentiles)

    nodes = pd.read_csv(nodes_path / f"{embryo_ID}_nodes.csv", index_col = 0)
    adj = pd.read_csv(nodes_path / f"{embryo_ID}_adj.csv", index_col = 0)
    adj.columns = adj.columns.astype(int)
    
    edge_weights = adj.values
    edge_weights = edge_weights[~np.isnan(edge_weights)]

    edge_dist = []

    for i in range(len(percentiles)+1):
        if i==0:
            count = len(edge_weights[edge_weights<=edge_percentiles[i]])
        elif i==len(percentiles):
            count = len(edge_weights[edge_weights>=edge_percentiles[i-1]])
        else:
            count = edge_weights[edge_percentiles[i-1]<=edge_weights]
            count = len(count<=edge_percentiles[i])
        print(count)
        print(len(nodes))
        edge_dist.append(count/len(nodes))

    percentiles2 = np.arange(0,110,10)
    plt.bar(percentiles2,edge_dist,width=5)

    plt.xlabel("Percentile")
    plt.ylabel("Edge Length Distribution")

    metadata_df = database.initialise_metadata()
    stage = metadata_df.loc[embryo_ID,"Stage"]
    plt.title(f"Edge Length Distribution of a HH{int(stage)} Embryo")


