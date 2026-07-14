import numpy as np
import pandas as pd
import tifffile as tiff
import seaborn as sns
import matplotlib.pyplot as plt

from config import processed_path, microns_per_pixel, main_image_path
import analysis
import database


def find_area(image,microns_per_pixel,threshold=0.85):
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

def get_pixel_neighbours(image,pixel):
    new_neighbours = []
    x,y = pixel
    neighbours = [[x-1,y-1], [x,y-1],[x-1,y],[x+1,y],[x,y+1],[x+1,y+1],[x-1,y+1],[x+1,y-1]]
    for i in neighbours:
        x_neigh, y_neigh = i
        if image[y_neigh][x_neigh]>0:
            new_neighbours.append([x_neigh,y_neigh])

    return new_neighbours

def find_components(image):
    height = len(image)
    width = len(image[0])
    
    components = pd.DataFrame(columns=["Area","Perimeter","Pixels"])

    pixel_list = []
    for x in range(1, width-1):
        for y in range(1, height-1):
            if image[y][x] >0:
                pixel_list.append([x,y])

    while pixel_list != []:
        comp_pixels = [pixel_list[0]]
        added = True
        while added:
            for i in comp_pixels:
                neighs = get_pixel_neighbours(image,i)
                #todo: add only the unique neighbours, stop when no new neighbours are added (has reached edge of component)


#This is inconsistent data handling with other code. It should save these area results to a new database and concat with metadata (master_df) to plot via sns
def normalised_area_graph(embryo_ID_list):
    area_df = pd.DataFrame(columns=["Stage","n","Condition","Area","Normalised Area"])
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

        area = find_area(image,microns_per_pixel)
        area_df.loc[embryo_ID,"Area"] = area
        area = normalise_area(area,embryo_ID)
        area_df.loc[embryo_ID,"Normalised Area"] = area
        

    sns.lineplot(data=area_df, x="Stage",y="Area", linewidth=2.5)

    plt.xlabel("HH Stage")
    plt.ylabel("Area ($\\mu m^2$)")

    plt.title(f"Area Distribution over Embryo Development")
    plt.show()

    sns.lineplot(data=area_df, x="Stage",y="Normalised Area", linewidth=2.5)
    plt.xlabel("HH Stage")
    plt.ylabel("Fractional Area (Normalised to Embryo Size)")

    plt.title(f"Area Distribution over Embryo Development")
