import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import pandas as pd
import numpy as np


#Change "4" to be the pixel_micron ratio
#merge these or fix datastructure setup later
def init_network_info_2d(nodes_list,adj_list,conditions):

    properties = ["Number of Nodes","Mean Edge Length","Mean Node Weight","Average Degree of Non-Isolated Nodes","Number of Basis Cycles","Number of Components","Average Clustering","Average Shortest Path","Number of Isolated Nodes","Number of Components, Excluding Isolated Nodes","Proportion of Isolated Nodes"]

    #2d datastructure
    df = pd.DataFrame(index=properties, columns=conditions)

    for i in range(len(conditions)):
        cond=conditions[i]
        print(f"Condition is: {cond}")

        nodes = nodes_list[i]
        adj = adj_list[i]

        adj = pd.DataFrame(adj)
        nodes = pd.DataFrame(nodes)

        df.loc["Number of Nodes",cond] = len(nodes)
        df.loc["Mean Edge Length",cond] = adj.values[adj.values>0].mean()
        df.loc["Mean Node Weight",cond] = np.mean(nodes["weight"])
        df.loc["Average Degree of Non-Isolated Nodes",cond] = count_neighbours(adj,min=1).mean()
        df.loc["Number of Isolated Nodes",cond] = np.array([count_neighbours(adj,min=0,max=100)==0]).sum()

        G=gen_networkx_graph(nodes,adj)
        print(f"Network generation complete\n")


        largest_cc = max(nx.connected_components(G), key=len)
        G_comp = G.subgraph(largest_cc).copy()


        df.loc["Number of Basis Cycles",cond] = len(sorted(nx.cycle_basis(G)))
        df.loc["Number of Components",cond] = len(sorted(nx.connected_components(G)))
        df.loc["Average Clustering",cond] = nx.average_clustering(G)
        df.loc["Average Shortest Path",cond] = nx.average_shortest_path_length(G_comp, weight='weight') #average shortest path of the largest component


        df.loc["Number of Components, Excluding Isolated Nodes",cond] = df.loc["Number of Components",cond] - df.loc["Number of Isolated Nodes",cond]
        df.loc["Proportion of Isolated Nodes", cond] = df.loc["Number of Isolated Nodes",cond] / df.loc["Number of Nodes",cond]

        xmin = nodes["x"].quantile(0.01)
        xmax = nodes["x"].quantile(0.99)
        df.loc["Mean Edge Length, Standardised",cond] = df.loc["Mean Edge Length",cond]/ (4*(xmax-xmin))

    return df

#Change "4" to be the pixel_micron ratio
def init_network_info_3d(nodes_all_stages,adj_all_stages,stages):
    properties = ["Number of Nodes","Mean Edge Length","Mean Node Weight","Average Degree of Non-Isolated Nodes","Number of Basis Cycles","Number of Components","Average Clustering","Average Shortest Path","Number of Isolated Nodes","Number of Components, Excluding Isolated Nodes","Proportion of Isolated Nodes"]
    max_n = 5
    n_list = range(max_n)

    #3d datastructure
    multi_cols = pd.MultiIndex.from_product([stages, n_list], names=['Stage', 'n'])
    df = pd.DataFrame(index=properties, columns=multi_cols)


    #set up properties that can be calculated directly

    n_node_weights = []
    n_neighbours_dists = []
    stage_index=0
    for i in range(len(stages)):
        stage=stages[i]

        for n in range(len(nodes_all_stages[i])):
            print(f"Stage: {stage}, n: {n}")
            nodes = nodes_all_stages[i][n]
            adj = adj_all_stages[i][n]


            adj = pd.DataFrame(adj)
            nodes = pd.DataFrame(nodes)

            df.loc["Number of Nodes",(stage,n)] = len(nodes)
            df.loc["Mean Edge Length",(stage,n)] = adj.values[adj.values>0].mean()
            df.loc["Mean Node Weight",(stage,n)] = np.mean(nodes["weight"])
            df.loc["Average Degree of Non-Isolated Nodes",(stage,n)] = count_neighbours(adj,min=1).mean()
            df.loc["Number of Isolated Nodes",(stage,n)] = np.array([count_neighbours(adj,min=0,max=100)==0]).sum()


            G=gen_networkx_graph(nodes,adj)
            print(f"Network generation complete\n")


            largest_cc = max(nx.connected_components(G), key=len)
            G_comp = G.subgraph(largest_cc).copy()


            df.loc["Number of Basis Cycles",(stage,n)] = len(sorted(nx.cycle_basis(G)))
            df.loc["Number of Components",(stage,n)] = len(sorted(nx.connected_components(G)))
            df.loc["Average Clustering",(stage,n)] = nx.average_clustering(G)
            df.loc["Average Shortest Path",(stage,n)] = nx.average_shortest_path_length(G_comp, weight='weight') #average shortest path of the largest component


            df.loc["Number of Components, Excluding Isolated Nodes",(stage,n)] = df.loc["Number of Components",(stage,n)] - df.loc["Number of Isolated Nodes",(stage,n)]
            df.loc["Proportion of Isolated Nodes", (stage,n)] = df.loc["Number of Isolated Nodes",(stage,n)] / df.loc["Number of Nodes",(stage,n)]

            xmin = nodes["x"].quantile(0.01)
            xmax = nodes["x"].quantile(0.99)
            df.loc["Mean Edge Length, Standardised",(stage,n)] = df.loc["Mean Edge Length",(stage,n)]/ (4*(xmax-xmin))



def mean_line(feature,df,stages):

    df = df.loc[feature]
    means = pd.Series(index=stages)

    for i in stages:
        stage_mean = df.loc[i].mean()
        #print(f"Stage is {i}, mean is {stage_mean}")
        means[i]=stage_mean

    return means

def plot_feature(feature,df,stages,title):
    # get the specific feature and drop any missing embryos (the nans)
    prop_data = df.loc[feature].dropna()

    # prop_data is now a Series. 
    # The index contains your (Stage, n) pairs.
    # The values contain your actual numbers.

    stages_n = prop_data.index.get_level_values('Stage') # Grabs just the Stage numbers for each n
    values = prop_data.values                          # Grabs the actual data points
    means = mean_line(feature,df,stages)

    plt.figure(figsize=(8, 5))
    plt.scatter(stages_n, values, alpha=0.7, edgecolors='black')
    plt.plot(stages,means,linewidth=3)

    plt.xlabel("HH Stage")
    plt.xticks(stages) # Ensures your X-axis only shows the actual stage numbers
    if feature== "Mean Edge Length":
        plt.ylabel(f"{feature} in $\\mu m$")
        plt.ylim(bottom=0)
    else:
        plt.ylabel(feature)
    if title!="":
        plt.title(f"{title} Per Embryo")
        plt.savefig(f'results/skeleton/main_figs_svgs/{title}.svg', transparent=True, dpi=300)
    else:
        plt.title(f"{feature} Per Embryo")
        plt.savefig(f'results/skeleton/main_figs_svgs/{feature}.svg', transparent=True, dpi=300)
    
    
    plt.show()

def plot_feature_drugs(feature,df,conditions,drug_name,means,means_label):
    # get the specific feature and drop any missing embryos (the nans)
    plt.figure(figsize=(8, 5))
    plt.scatter(conditions, df.loc[feature], alpha=0.7, edgecolors='black')
    #plt.plot(stages,means,linewidth=3)

    plt.xlabel("Drug Condition")
    if feature== "Mean Edge Length":
        plt.ylabel(f"{feature} in Microns")
    else:
        plt.ylabel(feature)

    if feature== "Number of Components":
        plt.ylim(top=600)

    plt.axhline(means[feature],label=f"{means_label} mean (no drugs)")
    plt.legend()
    plt.title(f"{drug_name}: {feature} per Embryo")
    #plt.xticks(stages) # Ensures your X-axis only shows the actual stage numbers
    plt.ylim(bottom=0)

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

def calc_degrees(adj,nodes):
    neighbours = adj.count()
    nodes["degree"] = neighbours
    return nodes

def calc_dists(adj,nodes):
    dists = adj.mean()
    nodes["distances"] = dists
    return nodes