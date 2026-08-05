# Vasculogenesis-Network-Skeleton



###### **Key Steps Summary**

1\. Run the preprocessing skeleton.ijm macro on the dataset (see setup below)

2\. Run the notebook code in run\_skeleton\_model.ipynb to 1. register metadata 2. initialise network files for each embryo 3. set up summary information for each embryo

3\. Run skeleton\_visualisation.ipynb to see if the skeleton models generated seem reasonable

4\. Use skeleton\_analysis\_results.ipynb, and files in additional\_notebooks to view and export analysis



###### **File naming conventions and data storage**

Embryos are strictly named in the format "hh\[stage]\_n\[replicate]\_\[condition] \[imagetype].tif", e.g.  "hh4\_n2\_10um BC.tif"

For a regular dataset (no drugs, no timeseries live imaging), "condition", is ignored, so the name becomes "hh4\_n2 BC.tif"

Different datasets (primary dataset, drug experiments, live imaging) are defined by folder naming: either "main" (primary dataset), "drugs/\[date]\_\[drug\_name]" e.g. "drugs/20240719\_MMP", or "live\_imaging"

Experiments are defined by their date (YYYYMMDD) and drug name, in the format "20240719\_MMP"



1. ###### **Preprocessing: skeleton.ijm and live\_imaging.ijm macros**

Run via Fiji/ImageJ



**Skeleton.ijm**: runs preprocessing for the skeleton network model, including scaling, measurements, contrast, adaptive local thresholding, skeletonisation.

Suitable for the main dataset and drug datasets (see below for live imaging)



**Setup**

1. Place images with the name "hh\[stage]\_n\[replicate]\_\[condition] BC.tif" into a folder ImageJ/raw/main or ImageJ/raw/drugs/\[date]\_\[drug\_name]. Create the save folder e.g. in python/data/raw/drugs/\[date]\_\[drug\_name]. Input files should be in the .tif format as a single image (not a stack, one channel), either the Hoescht or Runx stain (whichever has clearer blood islands. It is also fine to add the layers if it improves blood island visibility). There is no need to do any manual preprocessing before running the macro. The input should contain the image measurements in microns.

2\. Open the macro in Fiji/ImageJ and comment/uncomment the top filepath lines to point to the correct dataset (main or drug dataset).

3\. Check stages, n\_max, and conditions correctly include all stages, number of replicates, and drug conditions (it is fine to list extra conditions/stages).



**Parameter setup**



pix\_micron\_ratio = 0.25

Number of pixels per micron, so 1 pixel = 4 microns. It is important to fix this ratio across every image so that the skeletonisation algorithm is applied at the same resolution.



blur\_in\_microns = 7.5

Gaussian blur size in microns.



min\_particle\_size=900;

Minimum particle size in microns squared. Might seem high but 900=30^2 which is only 7.5x7.5 pixels (could easily be some debris).



local\_threshold\_radius=30;

Radius for local thresholding in pixels.





**Running and outputs**

Follow the macro instructions, which includes taking embryo measurements, adjusting brightness/contrast, and removing noise. The macro writes to the save path specified, either python/data/raw/main or python/data/raw/drugs/\[date]\_\[drug\_name].

Images that have already been processed are skipped.



The following outputs are saved:

python/data/imagej/**imageJ\_metadata.csv**: contains metadata and measurements that will be read by Python later.

python/data/raw/main/**particles.tif**: the thresholded particles file showing blood islands in white

python/data/raw/main/**skeleton.tif**: the iterative thinning skeleton file showing blood islands as one pixel wide paths

python/data/raw/main/**distmap.tif**: contains the distance map, representing the thickness of blood island regions

python/data/raw/main/**plain\_scaled.jpg**: just saves the high contrast file as a regular image, for reference of its quality and for visualisation



It is important to save and load these images as TIFF files to avoid compression artefacts (e.g. in JPEGs) and save numerical information (e.g. distmap stores the distances in microns as floating point numbers).





**Troubleshooting to improve image quality**

If image quality is poor, delete the output images from Python/data/raw/main or Python/data/raw/drugs/\[date]\_\[drug\_name]. If you want to rerun the measurement generation, delete the relevant line from imageJ\_metadata.csv. You can now try again.	



1. If the embryo is visible and brighter than the blood islands, it is recommended to delete it prior to thresholding, to avoid skewing histogram values.

2\. Low contrast mode - the normal local thresholding (Bernsen) uses a minimum contrast value (derived from the image histogram) to avoid thresholding noise or background edges. In the case of poor image quality (e.g. blood islands not showing up), turn on low contrast mode to skip this - but it will generate more background noise which requires manual deletion.

3\. Thin vessel mode is recommended for HH12/13 embryos, it uses Otsu thresholding which is more effective at detecting thin, low contrast vessels.



**Live\_imaging macro**

Same instructions as above, just adapted for stack processing. The input should be "hh\[stage]\_n\[replicate]\_\[condition] BC.tif" in the folder ImageJ/raw/live\_imaging, as a **stack**, corresponding to each time frame.





###### **2. Run\_skeleton\_model.ipynb and config.py**



The skeleton model  works as follows (stored in algorithms/skeleton\_model.py):

1. Reads any skeleton/distmap file stored in Python/data/raw/main (or drug folder)

2\. Identifies the location of nodes by finding junction points (>=3 neighbours) and end points (<=1 neighbours) in the skeleton image. Node weight is inherited from the distance map to measure the blood island thickness. Stores this as a nodes Pandas DataFrame, containing node\_id, x, y, weight.

3\. Traverses edges between nodes, finds their length and sets up an adjacency matrix adj. Identifies the average thickness of edges. Stores this as an edges Pandas DataFrame, containing edge\_id, start\_id, end\_id, length, thickness.

4\. Saves the nodes, adj, edges datastructures to .csv files in python/data/processed/skeleton\_networks



**Config.py:** contains the path configurations and core parameters for the skeleton model.



pix\_micron\_ratio = 0.25

Make sure this matches the ratio used in the skeleton.ijm macro.



base\_merge=6: intercept term in pixels

sensitivity\_merge=0.15: multiplier term (unitless)

Parameters for the node merging algorithm. The skeletonisation can generate nodes close together which are not biologically distinct. Nodes are merged according to the following criteria:

Merge node b into node a if: dist(a,b) <= weight\_a\*sensitivity\_merge + base\_merge\*microns\_per\_pixel

Where dist(a,b) is the length of the edge connecting a and b in microns, weight\_a is the thickness/weight of node a.



col\_threshold = 0.85

Is a tolerance threshold for interpretation of white pixels, so a "white" pixel has to be 85% white. If working with .tif files this threshold should not matter. It allows for slight errors in pixel value e.g. if a pixel is stored as \[253] instead of \[255].



**Run\_skeleton\_model.ipynb**

Contains 3 key steps to setting up the skeleton networks

1. Register embryo metadata from ImageJ. We set up a metadata\_df which assigns each embryo an embryo\_ID. This might seem complex but assigning a unique embryo\_ID is much easier for a computer to store and locate save files (e.g. vs long strings such as \[stage]\_\[n]\_\[experiment\_date]\_\[drug\_name]\_\[condition]. The measurement data is already generated from ImageJ, so algorithms/database.py just handles managing the embryo\_ID system to stop duplicate data etc.
2. Run the skeleton model and save csv's via form\_networks\_all.
3. Gather the summary statistics per embryo (e.g. number of components, number of cycles) and save in summary.csv.



###### **3. Visualisation**

skeleton\_visualisation.iypnb and algorithms/visualisation.py



Displays the skeleton network for one embryo per stage, e.g. for verifying the preprocessing and parameter fitting.

Later code uses the functions image\_plot and nodes\_plot to display zoomed regions e.g. for use in figures.

Both functions are designed to display a selected region, specified by size, x\_min, y\_min.

Useful for general testing.



###### **4. Analysis**



The core analysis is displayed in skeleton\_analysis\_results.ipynb, generated in algorithms/analysis.py

The code works as follows: use database.get\_embryo\_IDs\_from\_drug(), which returns a list of embryo\_IDs based on the drug condition provided (leave blank for normal dataset). Then call analysis.plot\_feature\_by\_stage() with a specified feature and the list of embryo\_IDs.



The plots are automatically saved as .svg and .png files if save=True, in the folder python/skeleton/results/skeleton\_analysis\_results/main



\[Description of each parameter generated]



Additional analysis files:

Area\_analysis\_results.ipynb: contains plots for the entire embryo size, blood island size and component distribution.

network\_type\_analysis\_results.ipynb: contains plots for the degree distribution and clustering coefficient per embryo.

spatial\_analysis.ipynb: splits the embryo into grid regions to compare spatial properties.





###### **Deletion**

You do not need to delete or rerun anything to add more embryos to the dataset. Just run the macro, then run\_skeleton\_model.ipynb. Preexisting files will be skipped to avoid redundant processing.



If you want to rerun the model, delete the .csv files from data/processed/skeleton\_networks, delete metadata.csv and summary.csv.

If you want to rerun the preprocessing and the model, delete the above, AND delete the files in python/data/raw/main (or drugs), and data/imagej/imageJ\_metadata.csv

