from config import data_path, imagej_metadata_path, processed_path
import pandas as pd
import numpy as np
from pathlib import Path

#todo: add a force overwrite option?

def initialise_metadata():
    #open the metadata file, or create one, if it doesn't exist
    file = Path(processed_path / "metadata.csv")
    if file.exists():
        metadata_df = pd.read_csv(file,index_col="Embryo_ID")
    else:
        metadata_df = pd.DataFrame(columns = ["Stage","n","Condition","Drug","Experiment_Date","Angle","Width","Height","Anterior_X","Anterior_Y","Ellipse_X","Ellipse_Y","Ellipse_W","Ellipse_H"])
    metadata_df.index.name = "Embryo_ID"
    return metadata_df

def get_embryo_ID(metadata_df,stage,n,condition=None):
    #Find a match for the embryo ID from the (stage,n,condition) data
    if condition == None or pd.isna(condition):
        index = metadata_df[(metadata_df["Stage"]==stage) & (metadata_df["n"]==n) & (pd.isna(metadata_df["Condition"]))].index
    else:
        index = metadata_df[(metadata_df["Stage"]==stage) & (metadata_df["n"]==n) & (metadata_df["Condition"]==condition)].index

    #return -1 if not found
    if len(index)==0:
        return -1
    if len(index)==1:
        return index[0]
    if len(index)>1:
        print("Error: multiple embryos defined with the same (stage,n,condition) tuple.")
        return -1 

def register_embryos_from_imageJ(metadata_df,drug=np.nan,exp_date=np.nan):
    #Generates database from .csv files provided by the ImageJ macro skeleton.ijm
    append_count = 0
    skip_count = 0

    #Define the file path
    if pd.isna(drug)  and pd.isna(exp_date):
        file = Path(imagej_metadata_path / "imageJ_metadata.csv")
    else:
        file = Path(imagej_metadata_path / f"{exp_date}_{drug}_imageJ_metadata.csv")

    if not file.exists():
        print(f"Error: cannot find metadata file: {file}")
        return metadata_df
    else:
        imageJ_metadata = pd.read_csv(file)
        print(f"Successfully opened metadata file: {file}")

        #Label the drug and experiment date
        imageJ_metadata["Drug"] = drug
        imageJ_metadata["Experiment_Date"] = exp_date
        for i in imageJ_metadata.index:
            row = imageJ_metadata.loc[i]

            if "Condition" in row.index:
                id = get_embryo_ID(metadata_df, row["Stage"], row["n"], row["Condition"])
            else:
                id = get_embryo_ID(metadata_df, row["Stage"], row["n"])

            if id == -1: #This embryo is not yet in the database, so add it
                append_count +=1
                new_id = int(np.nanmax([0,np.max(metadata_df.index)])+1)
                metadata_df.loc[new_id] = row
            else: # Embryo already in database
                skip_count += 1
        print(f"{skip_count} embryos were skipped (already in database), {append_count} new embryos were appended. Total count: {len(metadata_df.index)}")
        return metadata_df
    

def save_metadata(metadata_df):
    file = Path(processed_path / "metadata.csv")
    metadata_df.to_csv(file)


