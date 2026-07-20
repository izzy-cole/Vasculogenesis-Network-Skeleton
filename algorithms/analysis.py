import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import pandas as pd
import numpy as np
from pathlib import Path
import os
import seaborn as sns

import algorithms.database as database
from config import processed_path, microns_per_pixel

def initialise_summary():
    properties = ["Number of Nodes","Mean Edge Length","Mean Node Weight","Average Degree of Non-Isolated Nodes","Number of Basis Cycles",
                  "Number of Components","Average Clustering","Average Shortest Path", "Number of Isolated Nodes",
                  "Number of Components, Excluding Isolated Nodes","Proportion of Isolated Nodes"]
    #open the summary file, or create one, if it doesn't exist
    file = Path(processed_path / "summary.csv")
    if file.exists():
        summary_df = pd.read_csv(file,index_col="Embryo_ID")
    else:
        summary_df = pd.DataFrame(columns = properties)
    summary_df.index.name = "Embryo_ID"
    return summary_df


def save_summary(summary_df):
    file = Path(processed_path / "summary.csv")
    summary_df.to_csv(file)


def register_skeleton_summary_data():

    #load database
    nodes_path = processed_path / "skeleton_networks"
    summary_df = initialise_summary()

    for file_name in os.listdir(nodes_path):

         #Get embryo ID
         embryo_ID, end = file_name.split("_")
         if end=="nodes.csv":

            #check if already in databse
            if int(embryo_ID) in summary_df.index:
                print(f"Embryo {embryo_ID} found in summary database")
                #Todo: check if any statistics are missing, e.g. if a new column is added, then rerun the analysis.
            else:
                print(f"Embryo {embryo_ID} not found in summary database, generating and saving statistics")


                nodes = pd.read_csv(nodes_path / f"{embryo_ID}_nodes.csv", index_col = 0)
                adj = pd.read_csv(nodes_path / f"{embryo_ID}_adj.csv", index_col = 0)
                adj.columns = adj.columns.astype(int)

                #Process properties
                summary_df.loc[embryo_ID,"Number of Nodes"] = len(nodes)
                summary_df.loc[embryo_ID,"Mean Edge Length"] = adj.values[adj.values>0].mean()
                summary_df.loc[embryo_ID,"Mean Node Weight"] = np.mean(nodes["weight"])
                summary_df.loc[embryo_ID,"Average Degree of Non-Isolated Nodes"] = count_neighbours(adj,min=1).mean()
                summary_df.loc[embryo_ID,"Number of Isolated Nodes"] = np.array([count_neighbours(adj,min=0,max=100)==0]).sum()

                G=gen_networkx_graph(nodes,adj)
                #print(f"Network generation complete\n")

                cc = nx.connected_components(G)
                largest_cc = max(nx.connected_components(G), key=len,default=0)
                if largest_cc!=0:
                    G_comp = G.subgraph(largest_cc).copy()
                    summary_df.loc[embryo_ID,"Average Shortest Path"] = nx.average_shortest_path_length(G_comp, weight='weight') #average shortest path of the largest component

                summary_df.loc[embryo_ID,"Number of Basis Cycles"] = len(sorted(nx.cycle_basis(G)))
                summary_df.loc[embryo_ID,"Number of Components"] = len(sorted(nx.connected_components(G)))
                try:
                    summary_df.loc[embryo_ID,"Average Clustering"] = nx.average_clustering(G)
                except:
                    print("Error collecting clustering data")


                summary_df.loc[embryo_ID,"Number of Components, Excluding Isolated Nodes"] = summary_df.loc[embryo_ID,"Number of Components"] - summary_df.loc[embryo_ID,"Number of Isolated Nodes",]
                summary_df.loc[embryo_ID,"Proportion of Isolated Nodes"] = summary_df.loc[embryo_ID,"Number of Isolated Nodes"] / summary_df.loc[embryo_ID,"Number of Nodes"]

                xmin = nodes["x"].quantile(0.01)
                xmax = nodes["x"].quantile(0.99)
                summary_df.loc[embryo_ID,"Mean Edge Length, Standardised"] = summary_df.loc[embryo_ID,"Mean Edge Length"]/ (microns_per_pixel*(xmax-xmin))

                save_summary(summary_df)
    return summary_df


def load_master_df():
    #Combines the network summary data with metadata allowing for easy indexing
    metadata_df = database.initialise_metadata()
    summary_df = initialise_summary()
    
    #join them using embryo_id index
    master_df = metadata_df.join(summary_df, how="inner")
    return master_df

#Could combine stage/condition function
def plot_feature_by_stage(feature,title="",embryo_ID_list=None):

    master_df = load_master_df()

    #display only a subset of embryos if chosen
    if embryo_ID_list is not None:
        master_df = master_df.loc[embryo_ID_list]

    #remove any empty feature data (e.g. no cycles present)
    master_df = master_df.dropna(subset=[feature])
    sns.lineplot(data=master_df, x="Stage",y=feature, linewidth=2.5)
    plt.title(feature)
    

    plt.xlabel("HH Stage")
    if feature== "Mean Edge Length":
        plt.ylabel(f"{feature} in $\\mu m$")
        plt.ylim(bottom=0)

    if title!="":
        plt.title(f"{title} Per Embryo")
        #plt.savefig(f'results/skeleton/main_figs_svgs/{title}.svg', transparent=True, dpi=300)
    else:
        plt.title(f"{feature} Per Embryo")
        #plt.savefig(f'results/skeleton/main_figs_svgs/{feature}.svg', transparent=True, dpi=300)

    plt.show()

def plot_feature_by_condition(feature,title=None,embryo_ID_list=None):

    master_df = load_master_df()

    #display only a subset of embryos if chosen
    if embryo_ID_list != None:
        master_df = master_df.loc[embryo_ID_list]

    #remove any empty feature data (e.g. no cycles present)
    master_df = master_df.dropna(subset=[feature])
    sns.lineplot(data=master_df, x="Condition",y=feature, linewidth=2.5)
    plt.title(feature)
    

    plt.xlabel("HH Stage")
    if feature== "Mean Edge Length":
        plt.ylabel(f"{feature} in $\\mu m$")
        plt.ylim(bottom=0)

    if title is not None:
        plt.title(f"{title} Per Embryo")
        #plt.savefig(f'results/skeleton/main_figs_svgs/{title}.svg', transparent=True, dpi=300)
    else:
        plt.title(f"{feature} Per Embryo")
        #plt.savefig(f'results/skeleton/main_figs_svgs/{feature}.svg', transparent=True, dpi=300)

    plt.show()
   

##not sure this is working
def violins(df,nodes_all_stages):
    # 1. Create an empty list to hold all our individual dataframes
    all_dataframes = []

    # 2. Loop through every stage and every embryo
    for stage, embryos in enumerate(nodes_all_stages):
        for n, df in enumerate(embryos):
            
            # Make a copy so we don't accidentally modify your original data
            temp_df = df.copy()
            
            # 3. Add the metadata as new columns! 
            # This is the crucial step for Seaborn so it knows where each node came from.
            temp_df['HH Stage'] = stage
            temp_df['Embryo ID'] = n
            
            # Append this updated dataframe to our list
            all_dataframes.append(temp_df)

    # 4. Mash them all together into one giant DataFrame
    # ignore_index=True ensures we get a fresh set of row numbers from 0 to N
    flat_df = pd.concat(all_dataframes, ignore_index=True)

    # Let's verify it worked
    print(flat_df[['HH Stage', 'Embryo ID', 'weight']].head())



    plt.figure(figsize=(12, 6))

    # Plot the full distribution of node weights per stage
    sns.violinplot(
        data=flat_df, 
        x='HH Stage', 
        y='weight',          # Make sure this exactly matches your column name
        hue='Embryo ID',     # Optional: Splits the violins to show each embryo side-by-side
        palette='muted',
        inner='quartile'
    )

    plt.title('Distribution of Node Weights Across HH Stages')
    plt.ylabel('Node Weight')
    plt.xlabel('HH Stage')
    plt.show()

def gen_networkx_graph(nodes,adj):
    adj.columns = adj.columns.astype(int)
    G = nx.Graph()

    for i in nodes.index:
        node = nodes.loc[i]
        #G.add_node(i)#,weight=node["weight"])
        G.add_nodes_from([(i, {"x": int(node["x"]), "y": int(node["y"]), "weight":float(node["weight"])})])

    for i in adj.index:
        for j in adj.columns:
            weight = adj.loc[i,j]
            if weight>0:
                G.add_edge(i,j,weight=weight)
    #nx.draw(G, with_labels=True)
    return G


def count_neighbours(adj,min=0,max=999):
    adj = adj[adj>0]
    neighbours = adj.count()
    neighbours = neighbours[neighbours>=min]
    neighbours = neighbours[neighbours<=max]
    return neighbours


def return_neighbours(adj):
    adj = adj[adj>0]
    neighbours = adj.count()
    neighbours = pd.Series.value_counts(neighbours)
    return neighbours

def calc_degrees(nodes,adj):
    neighbours = adj.count()
    nodes["degree"] = neighbours
    return nodes

def calc_dists(nodes,adj):
    dists = adj.mean()
    nodes["distances"] = dists
    return nodes