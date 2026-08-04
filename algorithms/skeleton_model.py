import cv2
import numpy as np
import pandas as pd
import tifffile as tiff
from pathlib import Path
import os

import algorithms.database as database
from config import processed_path
from config import microns_per_pixel, base_merge, sensitivity_merge, col_threshold

def find_white_pixel_neighbours(image,x,y,white):
    """returns a list of adjacent white pixels"""

    offsets = [(1, 0), (0, 1), (-1, 0), (0, -1),   
            (1, 1), (-1, 1), (1, -1), (-1, -1)]

    #Define the threshold for what a white pixel is ()
    #white = [255*(1-col_threshold)]*3
    neighbours = []

    for i in offsets:
        #loop through neighbours
        new_x, new_y = x+i[0], y+i[1]
        if np.all(image[new_y,new_x] > white):
            neighbours.append([new_x,new_y])

    return neighbours


def traverse_edge(node_set,white_pixels,dists,nodes,path):
    """Start from a node, then traverse the pixel edge until another node is met.
    Updated: now records the edge thickness."""
    x_start,y_start = path[0][0], path[0][1]
    thickness  = dists[y_start,x_start]
    offsets = [(1, 0), (0, 1), (-1, 0), (0, -1),   
        (1, 1), (-1, 1), (1, -1), (-1, -1)]
   
    while True:
        #current x and y
        x=int(path[-1][0])
        y=int(path[-1][1])
        thickness += dists[y,x]

        #keep track of previous pixel to avoid backtracking
        prev=tuple(path[-2])

        #search for a match in the nodes list - the path is complete
        if (x,y) in node_set:
            thickness = thickness/(len(path)-1) #the edge thickness is the mean of all pixel thicknesses
            return path, thickness

        else: #if not found, complete main loop
            #find the next direction to travel in (that isn't going backwards)
            appended = False
            for i in offsets:
                neighbour = (x+i[0],y+i[1])
                if neighbour in white_pixels and neighbour!=prev: #found the next direction
                    path.append(neighbour)
                    appended = True
            if not appended:
                #Something has gone wrong: the path cannot be completed
                print("No path found")
                print(path)
                return path
            

def make_coord_to_id_dict(nodes):
    """Creates a dictionary for looking up (x,y) coordinates to node ID, because the dictionary lookup is much fast (O(1)) than using .loc on a pd dataframe."""
    xs = nodes["x"].values
    ys = nodes["y"].values 
    n = len(nodes.index)
    coord_to_id = {}
    for i in range(n):
        coord = (xs[i],ys[i])
        coord_to_id[coord] = i
    return coord_to_id

def coords_to_id(coord_to_id_dict, x, y):
    #Dictionary lookup from the given dictionary
    return coord_to_id_dict.get((x, y))

def nodes_edges_from_image(image,dists):
    """Receives a skeleton image and a distmap image and turns it into a network structure (nodes dataframe, edges dataframe, and adjacency matrix)."""

    #Make a copy and zero out the outer border pixels
    image = image.copy()
    image[0, :] = 0
    image[-1, :] = 0
    image[:, 0] = 0
    image[:, -1] = 0

    pix_neighbours = [] #keep temp track of white pixel neighbours

    height = len(image)
    width = len(image[0])
    white_pixels = []

    nodes_data = []

    #1. Node initialisation (determine which white pixels are nodes)
    n = 0
    white = 255*(1-col_threshold)
    for x in range(width):
        for y in range(height):
            #if pixel is white (within a tolerance threshold to allow for changes in colour due to compression)
            if image[y][x]> white: 
                white_pixels.append([x,y]) #form white pixel list
                neighbours = find_white_pixel_neighbours(image,x,y,white) #find neighbours
                #print(f"{x,y}'s neighbours are {neighbours}")

                count = len(neighbours)
                weight = dists[y][x] #get the node weight from the distance map

                if count > 2: #a junction
                    #print(f"coord {x,y} is a node with {count} neighbours and weight {weight} and adjacencies {neighbours}")

                    nodes_data.append({"x": x, "y": y, "type": "junction", "weight": weight})
                    pix_neighbours.append(neighbours)
                    n+=1

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
    white_pixels_set = set(tuple(p) for p in white_pixels)

    #2. Edge traversal (determine which nodes are connected to each other)
    edge_data = []
    for i in range(n):
        x1=nodes["x"].loc[i]
        y1=nodes["y"].loc[i]
        id1=i
        #for each neighbour, we traverse the path to find the node it is connected to
        for j in pix_neighbours[i]:
            path,thickness = traverse_edge(node_set,white_pixels_set,dists,nodes,path=[(x1,y1),tuple(j)])
            x2,y2 = path[-1]
            id2 = coords_to_id(coord_to_id_dict,x2,y2)
            #set the adjacency value as the length of the path in microns
            if id2 is not None:
                edge_len =  (len(path)-1)*microns_per_pixel#subtract one because the path includes both start and end points
                #Update datastructures
                adj.loc[id1,id2] = edge_len
                edge_data.append({"start_id": id1, "end_id": id2, "length": edge_len, "thickness": thickness})
            else:
                print("ID2 not found")

    edges = pd.DataFrame(edge_data)
    return nodes,adj,edges

def get_node_adjacencies(adj,id):
    #searches the 'id' row and returns any indexes with a nonzero value (so an adjancency)
    row = adj.loc[id]
    return row[row>0].index.tolist()

#Updated to work with edges datastructure
def merge_nearby_nodes(nodes,adj,edges):

    #Create a temporary thickness matrix to handle thickness data while node merging
    thickness_matrix = pd.DataFrame(index=adj.index, columns=adj.columns, dtype=float)
    for i in edges.index:
        row = edges.loc[i]
        thickness_matrix.loc[int(row["start_id"]), int(row["end_id"])] = row["thickness"]

    del_nodes_set = set()
    #'a' and 'b' are IDs of two nodes
    for a in nodes.index:

        #skip the nodes already deleted
        if a not in del_nodes_set:

            xa,ya,weight = nodes[["x","y","weight"]].loc[a] #get a's properties
            neighbours_a = get_node_adjacencies(adj,a)

            for b in neighbours_a:
                if b in del_nodes_set: #ignore if already deleted
                    continue

                dist = adj.loc[a,b]
                xb,yb = nodes[["x","y"]].loc[b]
                if dist <= weight*sensitivity_merge + base_merge*microns_per_pixel: #too close: will merge b into a
                    #print(f"Max dist is {weight*sensitivity}, distance {dist} from {xa,ya} to {xb,yb}")

                    neighbours_b=get_node_adjacencies(adj,b)

                    #loop through b's adjacencies (c values) to set up a's new adjacencies
                    for c in neighbours_b:
                        if c!=a and c not in del_nodes_set: #do not create a self loop
                            bc_edge = adj.loc[b,c]
                            ac_edge = adj.loc[a,c]
                            #print(f"a is {a}, b is {b}, c is {c}, bc_edge is {bc_edge}, ac_edge is {ac_edge}")

                            bc_edge_thickness = thickness_matrix.loc[b,c]

                            if adj.loc[a,c]>0: #a,c are already adjacent, so find the min distance
                                if bc_edge < ac_edge:
                                    adj.loc[a,c] = bc_edge
                                    adj.loc[c,a] = bc_edge

                                    thickness_matrix.loc[a, c] = bc_edge_thickness
                                    thickness_matrix.loc[c, a] = bc_edge_thickness
                                #else: #Redundant case: if ac_edge is shorter, the details are kept the same.
                                    #adj.loc[a,c] = min(bc_edge,ac_edge)
                                    #adj.loc[c,a] = min(bc_edge,ac_edge)
                                    #edges.loc[ac_edge_id,"thickness"] = bc_edge_thickness

                            else: #a and c are not adjacent, so a inherit's b's adjacency of c
                                adj.loc[a,c] = bc_edge
                                adj.loc[c,a] = bc_edge
                                thickness_matrix.loc[a, c] = bc_edge_thickness
                                thickness_matrix.loc[c, a] = bc_edge_thickness

                    del_nodes_set.add(b)
                    #print(f"{b} has been deleted")

    nodes = nodes.drop(index=list(del_nodes_set))
    adj = adj.drop(index=list(del_nodes_set), columns=list(del_nodes_set))

    #Recreate the edges dataframe
    edge_data = []
    for id1 in adj.index:
        for id2 in adj.columns:
            if adj.loc[id1, id2] > 0 and not np.isnan(adj.loc[id1, id2]): #The edge exists
                edge_data.append({
                    "start_id": id1,
                    "end_id": id2,
                    "length": adj.loc[id1, id2],
                    "thickness": thickness_matrix.loc[id1, id2]
                })

    edges = pd.DataFrame(edge_data)

    return nodes,adj,edges

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
                print(f"Error: unable to process file name {file_name}")


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
            if not (save_dir / f"{embryo_ID}_nodes.csv").exists() or not (save_dir / f"{embryo_ID}_adj.csv").exists():
                print(f"No existing file found for image HH{stage}, n{n} {condition}. Embryo ID: {embryo_ID}. Processing now.")

                height = len(skel)
                width = len(skel[0])
                print(f"Dimensions in pixels {width}x{height}")
                #print(f"There are {microns_per_pixel} microns per pixel")
                print(f"Dimensions in microns {width*microns_per_pixel}x{height*microns_per_pixel}")

                #set up node and edge matrices
                nodes,adj,edges = nodes_edges_from_image(skel,dists)
                print(f"Unmerged length:{len(nodes)}")

                #apply merging on nearby nodes
                nodes2,adj2,edges2 = merge_nearby_nodes(nodes,adj,edges)

                save_dir = processed_path / "skeleton_networks"

                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                nodes2.to_csv(save_dir / f"{embryo_ID}_nodes.csv")
                adj2.to_csv(save_dir / f"{embryo_ID}_adj.csv")
                edges2.to_csv(save_dir / f"{embryo_ID}_edges.csv")

                print(f"Merged length:{len(nodes2)}")
                print("\n")
            else:
                print(f"Existing file found for image HH{stage}, n{n} {condition}. Embryo ID: {embryo_ID}.")