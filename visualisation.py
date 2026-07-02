def image_plot(image,size,x_min=0,y_min=0):
    #show skeleton
    fig,ax=plt.subplots(figsize=(10,10))
    ax.imshow(image,cmap=plt.cm.gray)
    ax.axis('off') 

    x_max,y_max = x_min+size[0],y_min+size[1]

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)

    plt.show()

def nodes_plot(image,nodes,adj,size,node_alpha=0.4,edge_alpha=1,im_alpha=1,edge_weights=False,node_weights=False,x_min=0,y_min=0):
    #show skeleton
    fig,ax=plt.subplots(figsize=(10,10))
    ax.imshow(image,cmap=plt.cm.gray,alpha=im_alpha)
    ax.axis('off') 

    x_max,y_max = x_min+size[0],y_min+size[1]



    #calculate nodes and edges
    patches = []
    for i in nodes.index:
        x,y,weight,type = nodes[["x","y","weight","type"]].loc[i]
        if x_min<=x<=x_max and y_min<=y<=y_max: #only plot the valid region
            if type == "junction": #colourings
                circle = Circle((x, y), 1+weight/20,color="#e2342c")
            else: 
                circle = Circle((x, y), 1+weight/20,color="#f2ad00")
            patches.append(circle)

            #text labelling
            if node_weights and int(weight)!=76 and int(weight)!=70 and int(weight)!=12: #hacky line to remove overlapping numbers
                ax.text(x, y, str(int(weight)), ha='center', va='center', fontsize=20, color='white',font="arial",weight="bold")
            
            
    p = PatchCollection(patches, alpha=node_alpha,match_original=True)
    ax.add_collection(p)


    #code for edges
    for i in adj:
        for j in adj:
            dist = adj.loc[i,j]
            if dist>0:
                x1,y1=nodes[["x","y"]].loc[i]
                x2,y2=nodes[["x","y"]].loc[j]
                if x_min<=x1<=x_max and y_min<=y1<=y_max:
                    ax.plot([x1,x2],[y1,y2],alpha=edge_alpha,linewidth=5,color="tab:blue")

                    #text labelling
                    av_x,av_y = (x1+x2)/2, (y1+y2)/2
                    if edge_weights and int(dist)!=4 and int(dist)!=244:
                        ax.text(av_x, av_y, str(int(dist)), ha='left', va='bottom', fontsize=20, color='white' ,font="arial",weight="bold")


    

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)

    plt.show()


def display_network(net,name):
    #nx.draw(net,with_labels=True)

    new_net = Network(height="750px", width="100%", bgcolor="#1F1F1F", font_color="white")#,notebook=True)
    new_net.toggle_physics(False) #displays the network
    new_net.from_nx(net)
    
    #[nx.set_node_attributes(net,)]
    #new_net.save_graph(f"{name}")
    new_net.show(f"{name}")#,notebook=True)


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