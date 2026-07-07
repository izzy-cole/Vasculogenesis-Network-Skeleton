from config import data_path
import pandas as pd
from pathlib import Path

def initialise_metadata():
    file = Path(data_path + "processed/metadata.csv")
    if file.exists():
        metadata_df = pd.read_csv(file,index_col="Embryo_ID")
    else:
        metadata_df = pd.DataFrame(columns = ["Stage","n","Condition","Drug","Experiment_Date","Angle","Width","Height","Anterior_X","Anterior_Y","Ellipse_X","Ellipse_Y","Ellipse_W","Ellipse_H"])
    metadata_df.index.name = "Embryo_ID"
    return metadata_df


def register_embryos_from_imageJ(metadata_df,drug=None,exp_date=None):
    if drug== None and exp_date == None:
        file = Path(data_path + "temp/imageJ_metadata.csv")
    else:
        file = Path(data_path + f"temp/{exp_date}_{drug}_imageJ_metadata.csv")

    if not file.exists():
        print(f"Error: cannot find metadata file: {file}")
        return metadata_df
    else:
        imageJ_metadata = pd.read_csv(file)
        print(f"Successfully opened metadata file: {file}")

        imageJ_metadata["Drug"] = drug
        imageJ_metadata["Experiment_Date"] = exp_date
        metadata_df =  pd.concat([metadata_df,imageJ_metadata])
        metadata_df.index.name = "Embryo_ID"
        return metadata_df
    
        #todo: loop through imageJ_metadata, check if (stage,n,condition) already exists (do not append duplicates).
        #Assign a unique embryo_ID to each new row.

def save_metadata(metadata_df):
    file = Path(data_path + "processed/metadata.csv")
    metadata_df.to_csv(file)

metadata_df = initialise_metadata()
print(metadata_df)
metadata_df = register_embryos_from_imageJ(metadata_df)
print(metadata_df)
metadata_df = register_embryos_from_imageJ(metadata_df,drug="MMP",exp_date="04032026")
print(metadata_df)
metadata_df = register_embryos_from_imageJ(metadata_df,drug="MMP",exp_date="19072024")
print(metadata_df)
save_metadata(metadata_df)


