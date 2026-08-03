# Vasculogenesis-Network-Skeleton



###### **Quickstart guide**

1\. Run the skeleton.ijm macro on the dataset (see setup below)

2\. Configure file paths and parameters in config.py

3\. Run run\_skeleton\_model.ipynb to 1. register metadata 2. initialise network files for each embryo 3. set up summary information for each embryo

4\. Use skeleton\_analysis\_results.ipynb, skeleton\_visualisation.ipynb, spatial\_analysis.ipynb, area\_analysis\_results.iypnb to view visualisations of network changes



###### **File naming conventions and data storage**

Embryos are strictly named in the format "hh\[stage]\_n\[replicate]\_\[condition] \[imagetype].tif", e.g.  "hh4\_n2\_10um BC.tif"

For a regular dataset (no drugs, no timeseries live imaging), "condition", is ignored, so the name becomes "hh4\_n2 BC.tif"



**Config.py**



###### **Skeleton.ijm macro**

**Run via Fiji/ImageJ**

Description

Read in BC files

Output particles, skeleton, distmap, plain\_scaled



**Guide**

1. Configure paths to open and save images
2. Check stages, n\_max, and conditions are correctly set up (it is fine to include extra values)
3. Run the macro and follow the instructions given. If image quality is poor, delete the output files (images and metadata) and try again (see troubleshooting below)



**Parameter setup**

pix\_micron\_ratio = 0.25;

//gaussian blur parameter in microns

blur\_in\_microns = 7.5;

//minimum particle size in microns squared

min\_particle\_size=250;

//Radius for local thresholding in pixels

local\_threshold\_radius=30;



**Troubleshooting to improve image quality**

1. If the embryo is visible and brighter than the blood islands, it is recommended to delete it prior to thresholding, to avoid skewing histogram values.

2\. Low contrast mode - the normal local thresholding (Bernsen) uses a minimum contrast value (derived from the image histogram) to avoid thresholding noise or background edges. In the case of poor image quality (e.g. blood islands not showing up), turn on low contrast mode to skip this - but will require more manual deletion of background noise.

3\. Thin vessel mode ??



Deletion and data handling



File walkthrough

Skeleton\_visualisation

