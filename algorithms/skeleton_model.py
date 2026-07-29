import cv2
import numpy as np
import pandas as pd
import tifffile as tiff
from pathlib import Path
import os

import algorithms.database as database
from config import processed_path
from config import microns_per_pixel, base_merge, sensitivity_merge, col_threshold

def find_pixel_neighbours(image,x,y):
    #returns a list of adjacent white pixels
    white = [255*(1-col_threshold)]*3
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


def traverse(node_set,pixels,nodes,path):
   
    while True:
        #current x and y
        x=int(path[-1][0])
        y=int(path[-1][1])

        #keep track of previous pixel to avoid backtracking
        prev=tuple(path[-2])
        #print(x,y)

        #search for a match in the nodes list - the path is complete
        if (x,y) in node_set:
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
            

def make_coord_to_id_dict(nodes):
    xs = nodes["x"].values
    ys = nodes["y"].values 
    n = len(nodes.index)
    coord_to_id = {}
    for i in range(n):
        coord = (xs[i],ys[i])
        coord_to_id[coord] = i
    return coord_to_id

def coords_to_id(coord_to_id_dict, x, y):
    return coord_to_id_dict.get((x, y))

def nodes_edges_from_image(image,dists):

    nodes = pd.DataFrame(data=None, columns=["x","y","type","weight"]) #main datastructure
    #pix_neighbours = pd.Series(data=None) #keep temp track of white pixel neighbours
    pix_neighbours = []

    height = len(image)
    width = len(image[0])
    pixels = []

    nodes_data = []

    #set up the list of nodes
    n = 0
    white = 255*(1-col_threshold)
    for x in range(1, width-1):
        for y in range(1, height-1):
            if image[y][x]> white: #if pixel is white (within a tolerance threshold to allow for changes in colour due to compression)
                pixels.append([x,y]) #form pixel list
                neighbours = find_pixel_neighbours(image,x,y) #find neighbours
                #print(f"{x,y}'s neighbours are {neighbours}")
                count = len(neighbours)
                weight = dists[y][x] #get the node weight from the distance map
                

                if count > 2: #a junction
                    #print(f"coord {x,y} is a node with {count} neighbours and weight {weight} and adjacencies {neighbours}")

                    nodes_data.append({"x": x, "y": y, "type": "junction", "weight": weight})
                    pix_neighbours.append(neighbours)
                    n+=1
                    #print(f"junction {x,y}")

                elif count <= 1: #end point or single node
                    nodes_data.append({"x": x, "y": y, "type": "endpt", "weight": weight})

                    pix_neighbours.append(neighbours)
                    n+=1

    #Build dataframe at the end (faster than .loc)
    nodes = pd.DataFrame(nodes_data)
    coord_to_id_dict = make_coord_to_id_dict(nodes)
    node_set = set(coord_to_id_dict.keys())

    #set up adjacency matrix     
    adj = pd.DataFrame(data=np.full((n,n),np.nan))
    pixels_set = set(tuple(p) for p in pixels)
    for i in range(n):
        x1=nodes["x"].loc[i]
        y1=nodes["y"].loc[i]
        id1=i
        #for each neighbour, we traverse the path to find the node it is connected to
        for j in pix_neighbours[i]:
            path = traverse(node_set,pixels_set,nodes,[(x1,y1),tuple(j)])
            x2,y2 = path[-1]
            id2 = coords_to_id(coord_to_id_dict,x2,y2)
            #set the adjacency value as the length of the path in microns
            adj.loc[id1,id2] = (len(path)-1)*microns_per_pixel#subtract one because the path includes both start and end points

    return nodes,adj

def get_node_adjacencies(adj,id):
    #searches the 'id' row and returns any indexes with a nonzero value (so an adjancency)
    row = adj.loc[id]
    return row[row>0].index.tolist()


def merge_nearby_nodes(nodes,adj):

    del_set = set()
    #'a' and 'b' are IDs of two nodes
    for a in nodes.index:
        #print(f"a is {a}")
        #skip the nodes already deleted
        if a not in del_set:
            xa,ya,weight = nodes[["x","y","weight"]].loc[a] #simple naming
            neighbours_a = get_node_adjacencies(adj,a)
            #print(f"a's neighbours are {neighbours_a}")
            for b in neighbours_a:
                if b in del_set:
                    continue
                #print(f"b is {b}")
                dist = adj.loc[a,b]
                xb,yb = nodes[["x","y"]].loc[b]
                if dist <= weight*sensitivity_merge + base_merge*microns_per_pixel: #too close: will merge
                    #print(f"Max dist is {weight*sensitivity}, distance {dist} from {xa,ya} to {xb,yb}")

                    neighbours_b=get_node_adjacencies(adj,b)
                    #loop through b's adjacencies to set up a's new adjacencies
                    #print(f"b's neighbours are {neighbours_b}")
                    for c in neighbours_b:
                        if c!=a and c not in del_set: #do not create a self loop
                            bc_edge = adj.loc[b,c]
                            ac_edge = adj.loc[a,c]
                            if adj.loc[a,c]>0: #a,c are already adjacent, so find the min distance
                                adj.loc[a,c] = min(bc_edge,ac_edge)
                                adj.loc[c,a] = min(bc_edge,ac_edge)
                            else: #a and c are not adjacent, so a inherit's b's adjacency of c
                                adj.loc[a,c] = bc_edge
                                adj.loc[c,a] = bc_edge
                    
                    del_set.add(b)
                    #print(f"{b} has been deleted")

    nodes = nodes.drop(index=list(del_set))
    adj = adj.drop(index=list(del_set), columns=list(del_set))
    return nodes,adj

def form_networks_all(path,skips=[],drug=None):

    nodes_list = []
    adj_list = []

    for file_name in os.listdir(path):

        #Get the stage,n,condition from the file name
        data, end = file_name.split(" ")
        if end=="skeleton.tif":
            data = data.split("_")
            if len(data)==2:
                stage, n = data
                stage = int(stage[2:]) #Remove "hh" label
                n = int(n[1:]) #Remove "n" label
                condition = np.nan
                skel = tiff.imread(path / f"hh{stage}_n{n} skeleton.tif")
                dists = tiff.imread(path / f"hh{stage}_n{n} distmap.tif")
            elif len(data)==3:
                stage, n, condition = data
                stage = int(stage[2:]) #Remove "hh"
                n = int(n[1:]) #Remove "n"
                skel = tiff.imread(path / f"hh{stage}_n{n}_{condition} skeleton.tif")
                dists = tiff.imread(path / f"hh{stage}_n{n}_{condition} distmap.tif")
            else:
                print(f"Error: unknown file name {file_name}")


            if [stage,n,condition] in skips or [stage,n] in skips:
                print(f"Skipping {file_name}")
                continue

            if drug is None:
                embryo_ID = database.get_embryo_ID(stage,n)
            else:
                embryo_ID = database.get_embryo_ID(stage,n,condition,drug=drug)

            #form save directory if it doesnt exist yet
            save_dir = processed_path / "skeleton_networks"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            #save file not found, so run the skeleton model
            if not Path(save_dir / f"{embryo_ID}_nodes.csv").exists() or not Path(save_dir / f"{embryo_ID}_adj.csv").exists:
                print(f"No existing file found for image HH{stage}, n{n} {condition}. Embryo ID: {embryo_ID}. Procesing now.")

                height = len(skel)
                width = len(skel[0])
                print(f"Dimensions in pixels {width}x{height}")
                #print(f"There are {microns_per_pixel} microns per pixel")
                print(f"Dimensions in microns {width*microns_per_pixel}x{height*microns_per_pixel}")

                #set up node and edge matrices
                nodes,adj = nodes_edges_from_image(skel,dists)
                print(f"Unmerged length:{len(nodes)}")

                #apply merging on nearby nodes
                nodes2,adj2 = merge_nearby_nodes(nodes,adj)

                save_dir = processed_path / "skeleton_networks"

                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                nodes2.to_csv(save_dir / f"{embryo_ID}_nodes.csv")
                adj2.to_csv(save_dir / f"{embryo_ID}_adj.csv")

                print(f"Merged length:{len(nodes2)}")
                print("\n")
            else:
                print(f"Existing file found for image HH{stage}, n{n} {condition}. Embryo ID: {embryo_ID}.")