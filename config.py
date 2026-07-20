from pathlib import Path

data_path = Path("demo_data/")

imagej_metadata_path = data_path 

main_image_path = data_path / "preprocessed"
drugs_image_path = ""

processed_path = data_path / "processed" 


#spatial resolution: number of pixels per micron
#MAKE SURE this matches the ratio used in the skeleton.ijm macro!
pix_micron_ratio = 0.25
microns_per_pixel = 1/pix_micron_ratio #do not edit

base_merge=2 #intercept term
sensitivity_merge=0.08 #multiplier term

#permitted tolerance for black vs white (e.g. in case of compression artefacts)
col_threshold = 0.85


conditions = ["","_10um","_20um","_30um","_40um","_50um","_control"] #empty string allows for no conditions in non-drug case

 #input images MUST be .tiffs: the distance map information needs to be stored as 32 bit .tif data to record an objective measurement in microns