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
    #open the summary file, or create one, if it doesn't exist
    file = Path(processed_path / "summary.csv")
    if file.exists():
        summary_df = pd.read_csv(file,index_col="Embryo_ID")
    else:
        summary_df = pd.DataFrame()
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
         embryo_ID = int(embryo_ID)

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

                metadata_df = database.initialise_metadata()
                w = float(metadata_df.loc[embryo_ID, "Ellipse_W"])
                h = float(metadata_df.loc[embryo_ID, "Ellipse_H"])
                area = (np.pi * w/2 * h/2)

                # Generate Graph for network analysis
                G = gen_networkx_graph(nodes, adj)

                adj_arr = adj.fillna(0).values
                adj_arr[adj_arr < 0] = 0
                degrees = (adj_arr > 0).sum(axis=1)

                num_nodes = len(nodes)
                num_isolated = int((degrees == 0).sum())
                num_components = len(sorted(nx.connected_components(G)))
                num_cycles = len(sorted(nx.cycle_basis(G)))
                mean_edge_length = adj.values[adj.values>0].mean()

                components = list(nx.connected_components(G))
                largest_cc = max(components, key=len, default=None)
                av_shortest_path = np.nan
                if largest_cc!=0:
                    G_comp = G.subgraph(largest_cc)
                    av_shortest_path = nx.average_shortest_path_length(G_comp, weight='weight') #average shortest path of the largest component
                
                row_data = {
                "Embryo_ID": embryo_ID,
                "Number of Nodes": num_nodes,
                "Mean Edge Length": mean_edge_length,
                "Mean Node Weight": float(nodes["weight"].mean()),
                "Average Degree of Non-Isolated Nodes": count_neighbours(adj,min=1).mean(),
                "Number of Isolated Nodes": num_isolated,
                "Average Shortest Path": av_shortest_path, 
                "Number of Basis Cycles": num_cycles,
                "Number of Components": num_components,
                "Average Clustering": nx.average_clustering(G),
                "Number of Components, Excluding Isolated Nodes": num_components - num_isolated,
                "Number of Isolated Nodes / Nodes": num_isolated / num_nodes if num_nodes > 0 else np.nan,
                "Mean Edge Length / Width": mean_edge_length / w if w > 0 else np.nan,
                "Number of Nodes / Area": num_nodes / area if area > 0 else np.nan,
                "Basis Cycles / Area": num_cycles / area if area > 0 else np.nan,
                "Isolated Nodes / Area": num_isolated / area if area > 0 else np.nan,
            }

                new_df = pd.DataFrame([row_data]).set_index("Embryo_ID")
                summary_df = pd.concat([summary_df, new_df])
                save_summary(summary_df)
                print(f"Embryo {embryo_ID} statistics saved successfully.")
            
    return summary_df


def load_master_df():
    #Combines the network summary data with metadata allowing for easy indexing
    metadata_df = database.initialise_metadata()
    summary_df = initialise_summary()
    
    #join them using embryo_id index
    master_df = metadata_df.join(summary_df, how="inner")
    return master_df

#Could combine stage/condition function
def plot_feature_by_stage(feature,title="",embryo_ID_list=None,save_path=None):

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

    #Use the title provided, or if left blank, use the default feature name
    if title!="":
        plt.title(f"{title} Per Embryo")
        #plt.savefig(f'results/skeleton/main_figs_svgs/{title}.svg', transparent=True, dpi=300)
    else:
        plt.title(f"{feature} Per Embryo")
        #plt.savefig(f'results/skeleton/main_figs_svgs/{feature}.svg', transparent=True, dpi=300)

    if save_path is not None:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        if title!="":
            plt.savefig(save_path / f"{title}.svg", transparent=True,dpi=300)
            plt.savefig(save_path / f"{title}.png", transparent=True,dpi=300)
        else:
            plt.savefig(save_path / f"{feature}.svg", transparent=True,dpi=300)
            plt.savefig(save_path / f"{feature}.png", transparent=True,dpi=300)

    plt.show()

def plot_feature_by_condition(feature,title=None,embryo_ID_list=None,condition_order=None,save_path=None,live=False):

    master_df = load_master_df()
    drug = master_df.loc[int(embryo_ID_list[0]),"Drug"]

    #display only a subset of embryos if chosen
    if embryo_ID_list is not None:
        master_df = master_df.loc[embryo_ID_list]

    #remove any empty feature data (e.g. no cycles present)
    master_df = master_df.dropna(subset=[feature])

    #Sort condition ordering
    if condition_order is not None:

        #Replace "um" with the mu symbol
        for i in master_df.index:
            if master_df.loc[i,"Condition"].find("um")!=-1:
                master_df.loc[i,"Condition"] = master_df.loc[i,"Condition"].replace("um", " $ \mu m $")
        for i in range(len(condition_order)):
            if condition_order[i].find("um")!=-1:
                condition_order[i] = condition_order[i].replace("um", " $ \mu m $")
    
        #Convert conditiont to a categorial datatype, allowing it to be ordered
        master_df["Condition"] = pd.Categorical(master_df["Condition"], categories=condition_order, ordered=True)
        master_df = master_df.sort_values("Condition")

    sns.lineplot(data=master_df, x="Condition",y=feature, linewidth=2.5)
    plt.title(feature)

    #Set up relevant titles and labelling
    if live:
        plt.xlabel(f"Time Frame")
        ticks = np.arange(1,len(master_df.index)+1,int(len(master_df.index)/10))
        plt.xticks(ticks,ticks)
        if title!="":
            plt.title(f"Live Imaging: {title} Over Time")
        else:
            plt.title(f"Live Imaging: {feature} Over Time")
    else:
        plt.xlabel(f"{drug} Condition")

        if title !="":
            plt.title(f"{drug}: {title} Per Embryo")
        else:
            plt.title(f"{drug}: {feature} Per Embryo")


    if feature== "Mean Edge Length":
        plt.ylabel(f"{feature} in $\\mu m$")
        plt.ylim(bottom=0)
    
    #Save, if requested
    if save_path is not None:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        if title!="":
            plt.savefig(save_path / f"{title}.svg", transparent=True,dpi=300)
            plt.savefig(save_path / f"{title}.png", transparent=True,dpi=300)
        else:
            plt.savefig(save_path / f"{feature}.svg", transparent=True,dpi=300)
            plt.savefig(save_path / f"{feature}.png", transparent=True,dpi=300)

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

    adj_matrix = adj.fillna(0).values
    G = nx.from_numpy_array(adj_matrix)

    node_attributes = {}
    for i in nodes.index:
        node = nodes.loc[i]
        node_attributes[i] = {"x": int(node["x"]), "y": int(node["y"]), "weight":float(node["weight"])}
    nx.set_node_attributes(G,node_attributes)
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