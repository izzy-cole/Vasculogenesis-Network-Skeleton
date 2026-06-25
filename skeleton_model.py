import cv2
import numpy as np
import pandas as pd
import tifffile as tiff


def find_pixel_neighbours(image,x,y,threshold):
    #returns a list of adjacent pixels
    white = [255*(1-threshold)]*3
    neighbours = []
    if np.all(image[y][x-1] > white):
        neighbours.append([x-1,y])

    if np.all(image[y-1][x] > white):
        neighbours.append([x,y-1])

    if np.all(image[y-1][x-1] > white):
        neighbours.append([x-1,y-1])

    if np.all(image[y+1][x-1] > white):
        neighbours.append([x-1,y+1])
  
    if np.all(image[y-1][x+1] > white):
        neighbours.append([x+1,y-1])

    if np.all(image[y][x+1] > white):
        neighbours.append([x+1,y])

    if np.all(image[y+1][x] > white):
        neighbours.append([x,y+1])

    if np.all(image[y+1][x+1] > white):
        neighbours.append([x+1,y+1])

    return neighbours



def traverse(pixels,nodes,path):
    while True:
        #current x and y
        x=int(path[-1][0])
        y=int(path[-1][1])

        #keep track of previous pixel to avoid backtracking
        prev=tuple(path[-2])
        #print(x,y)

        #search for a match in the nodes list - the path is complete
        if len(nodes[(nodes["x"]==x) & (nodes["y"]==y)])>0:
            #print(f"Found end: {path[-1]}")
            return path
        
        else: #if not, complete main recursive loop
            #find the next direction to travel in (that isn't going backwards)
            if (x-1,y) in pixels and (x-1,y)!=prev: 
                path.append((x-1,y))
            elif (x,y-1) in pixels and (x,y-1)!=prev:
                path.append((x,y-1))
            elif (x-1,y-1) in pixels and (x-1,y-1)!=prev:
                path.append((x-1,y-1))
            elif (x-1,y+1) in pixels and (x-1,y+1)!=prev:
                path.append((x-1,y+1))
            elif (x+1,y-1) in pixels and (x+1,y-1)!=prev:
                path.append((x+1,y-1))
            elif (x+1,y) in pixels and (x+1,y)!=prev:
                path.append((x+1,y))
            elif (x,y+1) in pixels and (x,y+1)!=prev:
                path.append((x,y+1))
            elif (x+1,y+1) in pixels and (x+1,y+1)!=prev:
                path.append((x+1,y+1))
            else:
                print("No path found")
                print(path)
                return path
            


def coords_to_id(nodes,x,y):
   return nodes[(nodes["x"]==x) & (nodes["y"]==y)].index



def nodes_edges_from_image(image,dists,threshold,microns_per_pixel):

    nodes = pd.DataFrame(data=None, columns=["x","y","type","weight"]) #main datastructure
    pix_neighbours = pd.Series(data=None) #keep temp track of white pixel neighbours

    height = len(image)
    width = len(image[0])
    pixels = []

    #set up the list of nodes
    n = 0
    for x in range(1, width-1):
        for y in range(1, height-1):

            if np.all(image[y][x]> [255*(1-threshold)]*3): #if pixel is white (within a tolerance threshold to allow for changes in colour due to compression)
                pixels.append([x,y]) #form pixel list
                neighbours = find_pixel_neighbours(image,x,y,threshold) #find neighbours
                #print(f"{x,y}'s neighbours are {neighbours}")
                count = len(neighbours)
                weight = dists[y][x] #get the node weight from the distance map
                

                if count > 2: #a junction
                    #print(f"coord {x,y} is a node with {count} neighbours and weight {weight} and adjacencies {neighbours}")
                    type="junction"
                    nodes.loc[n] = {"x":x,"y":y,"type":type,"weight":weight}
                    pix_neighbours.loc[n] = neighbours
                    n+=1
                    #print(f"junction {x,y}")

                elif count <= 1: #end point or single node
                    type="endpt"
                    nodes.loc[n] = {"x":x,"y":y,"type":type,"weight":weight}
                    pix_neighbours.loc[n] = neighbours
                    n+=1


    #set up adjacency matrix     
    adj = pd.DataFrame(data=np.full((n,n),np.nan))
    pixels_set = set(tuple(p) for p in pixels)
    for i in range(n):
        x1=nodes["x"].loc[i]
        y1=nodes["y"].loc[i]
        id1=i
        #for each neighbour, we traverse the path to find the node it is connected to
        for j in pix_neighbours.loc[i]:
            path = traverse(pixels_set,nodes,[(x1,y1),tuple(j)])
            x2,y2 = path[-1]
            id2 = coords_to_id(nodes,x2,y2)
            #set the adjacency value as the length of the path in microns
            adj.loc[id1,id2] = (len(path)-1)*microns_per_pixel#subtract one because the path includes both start and end points

    return nodes,adj


def get_node_adjacencies(adj,id):
    #searches the 'id' row and returns any indexes with a nonzero value (so an adjancency)
    return [i for i in adj.index if adj.loc[id,i]>0]


def merge_nearby_nodes(nodes,adj,sensitivity,base,microns_per_pixel):

    del_list = []
    #'a' and 'b' are IDs of two nodes
    for a in nodes.index:
        #print(f"a is {a}")
        #skip the nodes already deleted
        if a not in del_list:
            xa,ya,weight = nodes[["x","y","weight"]].loc[a] #simple naming
            neighbours_a = get_node_adjacencies(adj,a)
            #print(f"a's neighbours are {neighbours_a}")
            for b in neighbours_a:
                #print(f"b is {b}")
                dist = adj.loc[a,b]
                xb,yb = nodes[["x","y"]].loc[b]
                if dist <= weight*sensitivity + base*microns_per_pixel: #too close: will merge
                    #print(f"Max dist is {weight*sensitivity}, distance {dist} from {xa,ya} to {xb,yb}")

                    neighbours_b=get_node_adjacencies(adj,b)
                    #loop through b's adjacencies to set up a's new adjacencies
                    #print(f"b's neighbours are {neighbours_b}")
                    for c in neighbours_b:
                        if not c==a: #do not create a self loop
                            if adj.loc[a,c]>0: #a,c are already adjacent, so find the min distance
                                adj.loc[a,c] = min(adj.loc[b,c],adj.loc[a,c])
                                adj.loc[c,a] = min(adj.loc[b,c],adj.loc[a,c])
                            else: #a and c are not adjacent, so a inherit's b's adjacency of c
                                adj.loc[a,c] = adj.loc[b,c]
                                adj.loc[c,a] = adj.loc[b,c]
                    
                    #adj = np.delete(adj,b,0)
                    #adj =np.delete(adj,b,1)
                    adj = adj.drop([b])
                    adj = adj.drop([b],axis=1)
                    nodes = nodes.drop([b])
                    del_list.append(b)
                    #print(f"{b} has been deleted")
        else:
            a=1
            #print(f"skipping {a} - it has been deleted")
    return nodes,adj

def form_networks_all(stages,path,microns_per_pixel,compression=1,threshold=0.85,base=1,dist_propn=0.1):

    nodes_all_stages = []
    adj_all_stages = []

    for stage in stages:
        nodes_list = []
        adj_list = []
        print(f"Stage is {stage}")
        n=1
        n_maxxed = False #repeat until files cannot be found
        while not n_maxxed:
            #input images MUST be .tiffs: the distance map information needs to be stored as 32 bit .tif data to record an objective measurement in microns

            try:
                image = tiff.imread(f'{path}n{n}_hh{stage}_skeleton.tif')
                dists = tiff.imread(f"{path}n{n}_hh{stage}_distmap.tif")
            except:  #file not found
                n_maxxed=True
                nodes_all_stages.append(nodes_list)
                adj_all_stages.append(adj_list)       

            else:
                print(f"Image HH{stage}, n={n}")

                #apply image compression: compression should NOT be used for skeleton images (set param to 1)
                image = cv2.resize(image, None, fx=compression,fy=compression)
                dists = cv2.resize(dists, None, fx=compression,fy=compression)

                height = len(image)
                width = len(image[0])
                print(f"Dimensions in pixels {width}x{height}")
                #print(f"There are {microns_per_pixel} microns per pixel")
                print(f"Dimensions in microns {width*microns_per_pixel}x{height*microns_per_pixel}")

                #set up node and edge matrices
                nodes,adj = nodes_edges_from_image(image,dists,threshold,microns_per_pixel)
                print(f"Unmerged length:{len(nodes)}")
                #visualise_image(image,dists,nodes,adj)


                #apply merging on nearby nodes
                nodes2,adj2 = merge_nearby_nodes(nodes,adj,dist_propn,base,microns_per_pixel)
                nodes_list.append(nodes2)
                adj_list.append(adj2)
                print(f"Merged length:{len(nodes2)}")
                #visualise_image(image,dists,nodes2,adj2)
                print("\n")
            n=n+1


    return nodes_all_stages, adj_all_stages
