import numpy as np
import pandas as pd
import tifffile as tiff
import seaborn as sns
import matplotlib.pyplot as plt

from config import processed_path, microns_per_pixel, main_image_path
import algorithms.analysis as analysis
import algorithms.database as database


def find_area(image):
    height = len(image)
    width = len(image[0])
    pixel_count = 0
    n = 0
    for x in range(1, width-1):
        for y in range(1, height-1):
            if image[y][x] >0 :
                pixel_count += 1

    area = pixel_count * ((microns_per_pixel) ** 2)
    return area

def normalise_area(area,embryo_ID):
    #Get the width nd height in microns
    metadata_df=database.initialise_metadata()
    w = metadata_df.loc[embryo_ID,"Ellipse_W"]
    h = metadata_df.loc[embryo_ID,"Ellipse_H"]
    return area / (np.pi * w/2 * h/2)

def find_components(image):
    height = len(image)
    width = len(image[0])
    
    components = pd.DataFrame(columns=["Area","Perimeter","Pixels"])
    offsets = [[-1,-1], [0,-1],[-1,0],[1,0],[0,1],[1,1],[-1,1],[1,-1]]

    visited = set()
    all_components = []
    pixel_list = []
    for x in range(width):
        for y in range(height):

            pix = (x,y)
            if image[y][x] > 0 and pix not in visited:
                #form new component tracking list
                comp_pixels = []
                check_queue = [pix]
                visited.add(pix)

                while len(check_queue)>0:
                    new_pix = check_queue.pop(0)
                    comp_pixels.append(new_pix)

                    for i in offsets:
                        x_0,y_0 = new_pix
                        x_neigh= x_0 + i[0]
                        y_neigh = y_0 + i[1]
                        if 0 <= x_neigh < width and 0<= y_neigh < height: #account for border pixels
                            if image[y_neigh][x_neigh]>0 and (x_neigh,y_neigh) not in visited:
                                visited.add((x_neigh,y_neigh))
                                check_queue.append((x_neigh,y_neigh))

                all_components.append(comp_pixels)
    return all_components

def component_dists(image):
    all_components = find_components(image)
    dists = []
    for i in all_components:
        dists.append(len(i)*((microns_per_pixel) ** 2))
    return dists


#This is inconsistent data handling with other code. It should save these area results to a new database and concat with metadata (master_df) to plot via sns
def normalised_area_graph(embryo_ID_list):
    area_df = pd.DataFrame(columns=["Stage","n","Condition","Area","Normalised Area","Area Distribution"])
    for embryo_ID in embryo_ID_list:
        metadata_df=database.initialise_metadata()
        n = int(metadata_df.loc[embryo_ID,"n"])
        stage = int(metadata_df.loc[embryo_ID,"Stage"])
        condition = metadata_df.loc[embryo_ID,"Condition"]
        if pd.isna(condition):
            image = tiff.imread(main_image_path / f"hh{stage}_n{n} particles.tif")
        else:
            image = tiff.imread(main_image_path / f"hh{stage}_n{n}_{condition} particles.tif")
        
        area_df.loc[embryo_ID,"Stage"] = stage
        area_df.loc[embryo_ID,"n"] = n
        area_df.loc[embryo_ID,"Condition"] = condition

        area = find_area(image)
        area_df.loc[embryo_ID,"Area"] = area
        area = normalise_area(area,embryo_ID)
        area_df.loc[embryo_ID,"Normalised Area"] = area
        

    sns.lineplot(data=area_df, x="Stage",y="Area", linewidth=2.5)

    plt.xlabel("HH Stage")
    plt.ylabel("Area ($\\mu m^2$)")

    plt.title(f"Blood Island Area over Embryo Development")
    plt.show()

    sns.lineplot(data=area_df, x="Stage",y="Normalised Area", linewidth=2.5)
    plt.xlabel("HH Stage")
    plt.ylabel("Fractional Area (Normalised to Embryo Size)")

    plt.title(f"Blood Island Area over Embryo Development")
    plt.show()

def area_distribution_plot(embryo_ID):
    metadata_df=database.initialise_metadata()
    n = int(metadata_df.loc[embryo_ID,"n"])
    stage = int(metadata_df.loc[embryo_ID,"Stage"])
    condition = metadata_df.loc[embryo_ID,"Condition"]
    if pd.isna(condition):
        image = tiff.imread(main_image_path / f"hh{stage}_n{n} particles.tif")
    else:
        image = tiff.imread(main_image_path / f"hh{stage}_n{n}_{condition} particles.tif")


    dist = component_dists(image)

    plt.hist(np.log(dist),bins=20)

    plt.xlabel("Log Blood Island Cluster Size ($\\mu m^2$)")
    plt.ylabel("Number of Clusters")
    plt.title(f"Blood Island Cluster Size Distribution for a HH{stage} Embryo")

    plt.xlim(3,18)
    plt.show()