from pathlib import Path

data_path = Path("C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/")

imagej_metadata_path = data_path / "imagej"

main_image_path = data_path / "raw" / "main" 
drugs_image_path = data_path / "raw" / "drugs" 

processed_path = data_path / "processed" 


#spatial resolution: number of pixels per micron
#MAKE SURE this matches the ratio used in the skeleton.ijm macro!
pix_micron_ratio = 0.25
microns_per_pixel = 1/pix_micron_ratio #do not edit

base_merge=2 #intercept term
sensitivity_merge=0.08 #multiplier term

#permitted tolerance for black vs white (e.g. in case of compression artefacts)
col_threshold = 0.85
