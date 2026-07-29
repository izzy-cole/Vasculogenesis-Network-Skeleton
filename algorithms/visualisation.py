from pyvis.network import Network
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.patches import Circle

def image_plot(image,size,x_min=0,y_min=0):
    #show skeleton
    fig,ax=plt.subplots(figsize=(10,10))

    x_max,y_max = x_min+size[0],y_min+size[1]

    #Crop before rendering the image to save processing
    image_crop = image[y_min:y_max, x_min:x_max]
    ax.imshow(image_crop, cmap=plt.cm.gray, extent=[x_min, x_max, y_max, y_min])

    ax.axis('off') 
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)

    plt.show()

def nodes_plot(image,nodes,adj,size,node_alpha=0.4,edge_alpha=1,im_alpha=1,edge_weights=False,node_weights=False,x_min=0,y_min=0,node_scaling=1,edge_scaling=1):
    fig,ax=plt.subplots(figsize=(10,10))
    x_max,y_max = x_min+size[0],y_min+size[1]

    if image is not None:
        #image_crop = image[y_min:y_max, x_min:x_max]
        ax.imshow(image,cmap=plt.cm.gray,alpha=im_alpha)
    else:
        print("No image")
        ax.set_facecolor("black")
    ax.set_xticks([])
    ax.set_yticks([])


    #calculate nodes and edges
    patches = []
    
    for i in nodes.index:
        x,y,weight,type = nodes[["x","y","weight","type"]].loc[i]
        if x_min<=x<=x_max and y_min<=y<=y_max: #only plot the valid region
            if type == "junction": #colourings
                circle = Circle((x, y), 1+weight*node_scaling/20,color="#e2342c")
            else: 
                circle = Circle((x, y), 1+weight*node_scaling/20,color="#f2ad00")
            patches.append(circle)

            #text labelling
            if node_weights: #hacky line to remove overlapping numbers
                ax.text(x, y, str(int(weight)), ha='center', va='center', fontsize=20, color='white',font="arial",weight="bold")
            
            
    pc = PatchCollection(patches, alpha=node_alpha,match_original=True)
    ax.add_collection(pc)

    lines = []
    #code for edges
    for i in adj:
        for j in adj:
            #avoid plotting twice (symmetric adj matrix)
            if i>j:
                dist = adj.loc[i,j]
                if dist>0:
                    x1,y1=nodes[["x","y"]].loc[i]
                    x2,y2=nodes[["x","y"]].loc[j]
                    #Check range
                    if x_min<=x1<=x_max and y_min<=y1<=y_max:
                        lines.append([[x1,y1],[x2,y2]])

                        #text labelling
                        av_x,av_y = (x1+x2)/2, (y1+y2)/2
                        if edge_weights:
                            ax.text(av_x, av_y, str(int(dist)), ha='left', va='bottom', fontsize=20, color='white' ,font="arial",weight="bold")

    lc = LineCollection(lines, colors="tab:blue", alpha=edge_alpha, linewidths=5*edge_scaling, zorder=2)
    ax.add_collection(lc)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)
    plt.show()


#cant get it to display in notebook (saves only)
def gen_pyvis_graph(nodes,adj,name,weight_divisor=50):
    G = Network(height="750px", width="100%", bgcolor="#1F1F1F", font_color="white",notebook=True)
    G.toggle_physics(False)

    for i in nodes.index:
        node = nodes.loc[i]
        G.add_node(i,label=i,size=float(node["weight"])/weight_divisor,x=int(node["x"]),y=int(node["y"]))

    for i in adj.index:
        for j in adj.columns:
            edge_weight = adj.loc[i,j]
            if edge_weight>0:
                G.add_edge(i,j,weight=float(edge_weight))
                if i==j:
                    print(f"edge between {i} and {j}")

    if name[-5:] != ".html":
        name = name + ".hmtl"

    G.show(f"{name}")
    return G