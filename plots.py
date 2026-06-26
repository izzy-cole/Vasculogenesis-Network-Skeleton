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

    plt.axhline(means[feature],label=f"{means_label} mean (no drugs)")
    plt.legend()
    plt.title(f"{drug_name}: {feature} per Embryo")
    #plt.xticks(stages) # Ensures your X-axis only shows the actual stage numbers
    plt.ylim(bottom=0)

    plt.show()

   
def gen_pyvis_graph(nodes,adj,name):
    G = Network(height="750px", width="100%", bgcolor="#1F1F1F", font_color="white",notebook=True)
    G.toggle_physics(False)
    for i in nodes.index:
        node = nodes.loc[i]
        G.add_node(i,label=i,size=float(node["weight"])/50,x=int(node["x"]),y=int(node["y"]))
        #G.add_nodes_from([(i, {"x": int(node["x"]), "y": int(node["y"]), "weight":float(node["weight"])})])
    for i in adj.index:
        for j in adj.columns:
            edge_weight = adj.loc[i,j]
            if edge_weight>0:
                G.add_edge(i,j,weight=float(edge_weight))
                if i==j:
                    print(f"edge between {i} and {j}")
    #nx.draw(G, with_labels=True)
    G.show(f"{name}")#,notebook=True)
    return G

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

def display_network(net,name):
    #nx.draw(net,with_labels=True)

    new_net = Network(height="750px", width="100%", bgcolor="#1F1F1F", font_color="white")#,notebook=True)
    new_net.toggle_physics(False) #displays the network
    new_net.from_nx(net)
    
    #[nx.set_node_attributes(net,)]
    #new_net.save_graph(f"{name}")
    new_net.show(f"{name}")#,notebook=True)