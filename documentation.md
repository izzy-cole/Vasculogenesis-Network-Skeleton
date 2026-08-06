# Vasculogenesis-Network-Skeleton



###### **Key Steps Summary**

1\. Run the preprocessing *skeleton.ijm* macro on the dataset (see setup below)

2\. Run the notebook code in *run\_skeleton\_model.ipynb* to 1. register metadata 2. initialise network files for each embryo 3. set up summary information for each embryo

3\. Run *skeleton\_visualisation.ipynb* to see if the skeleton models generated seem reasonable

4\. Use *skeleton\_analysis\_results.ipynb*, and files in additional\_notebooks to view and export analysis



###### **File naming conventions and data storage**

Embryos are strictly named in the format "*hh\[stage]\_n\[replicate]\_\[condition] \[imagetype].tif*", e.g.  "*hh4\_n2\_10um BC.tif"*

For a regular dataset (no drugs, no timeseries live imaging), "condition", is ignored, so the name becomes "hh4\_n2 BC.tif"

Different datasets (primary dataset, drug experiments, live imaging) are defined by folder naming: either "main" (primary dataset), "*drugs/\[date]\_\[drug\_name]*" e.g. "*drugs/20240719\_MMP*", or "*live\_imaging*"

Experiments are defined by their date (YYYYMMDD) and drug name, in the format "*20240719\_MMP*"



###### **1. Preprocessing: skeleton.ijm and live\_imaging.ijm macros**

Run via Fiji/ImageJ



**Skeleton.ijm**: runs preprocessing for the skeleton network model, including scaling, measurements, contrast, adaptive local thresholding, skeletonisation.

Suitable for the main dataset and drug datasets (see below for live imaging)



**Setup**

1. Place images with the name "*hh\[stage]\_n\[replicate]\_\[condition] BC.tif*" into a folder *ImageJ/raw/main* or *"ImageJ/raw/drugs/\[date]\_\[drug\_name]"*. Create the save folder e.g. in "*python/data/raw/drugs/\[date]\_\[drug\_name]*". Input files should be in the .tif format as a single image (not a stack, one channel), either the Hoescht or Runx stain (whichever has clearer blood islands. It is also fine to add the layers if it improves blood island visibility). There is no need to do any manual preprocessing before running the macro. The input should contain the image measurements in microns.

2\. Open the macro in Fiji/ImageJ and comment/uncomment the top filepath lines to point to the correct dataset (main or drug dataset). So there should be a defined *main\_path*, *save\_path*, and *csv\_path*.

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

Follow the macro instructions, which includes taking embryo measurements, adjusting brightness/contrast, and removing noise. The macro writes to the save path specified, either *python/data/raw/main* or "*python/data/raw/drugs/\[date]\_\[drug\_name]*".

Images that have already been processed are skipped.



The following outputs are saved:

python/data/imagej/**imageJ\_metadata.csv**: contains metadata and measurements that will be read by Python later.

python/data/raw/main/**particles.tif**: the thresholded particles file showing blood islands in white

python/data/raw/main/**skeleton.tif**: the iterative thinning skeleton file showing blood islands as one pixel wide paths

python/data/raw/main/**distmap.tif**: contains the distance map, representing the thickness of blood island regions

python/data/raw/main/**plain\_scaled.jpg**: just saves the high contrast file as a regular image, for reference of its quality and for visualisation



It is important to save and load these images as TIFF files to avoid compression artefacts (e.g. in JPEGs) and save numerical information (e.g. distmap stores the distances in microns as floating point numbers).





**Troubleshooting to improve image quality**

If image quality is poor, delete the output images from *Python/data/raw/main* or *"Python/data/raw/drugs/\[date]\_\[drug\_name]*". If you want to rerun the measurement generation, delete the relevant line from *imageJ\_metadata.csv*. You can now try again.



1. If the embryo is visible and brighter than the blood islands, it is recommended to delete it prior to thresholding, to avoid skewing histogram values.

2\. Low contrast mode - the normal local thresholding (Bernsen) uses a minimum contrast value (derived from the image histogram) to avoid thresholding noise or background edges. In the case of poor image quality (e.g. blood islands not showing up), turn on low contrast mode to skip this - but it will generate more background noise which requires manual deletion.

3\. Thin vessel mode is recommended for HH12/13 embryos, it uses Otsu thresholding which is more effective at detecting thin, low contrast vessels.



**Live\_imaging macro**

Same instructions as above, just adapted for stack processing. The input should be "*hh\[stage]\_n\[replicate]\_\[condition] BC.tif*" in the folder *ImageJ/raw/live\_imaging*, as a **stack**, corresponding to each time frame.





###### **2. Model generation**



The skeleton model  works as follows (stored in *algorithms/skeleton\_model.py*):

1. Reads any skeleton/distmap file stored in Python/data/raw/main (or drug folder)

2\. Identifies the location of nodes by finding junction points (>=3 neighbours) and end points (<=1 neighbours) in the skeleton image. Node weight is inherited from the distance map to measure the blood island thickness. Stores this as a nodes Pandas DataFrame, containing node\_id, x, y, weight.

3\. Traverses edges between nodes, finds their length and sets up an adjacency matrix adj. Identifies the average thickness of edges. Stores this as an edges Pandas DataFrame, containing edge\_id, start\_id, end\_id, length, thickness.

4\. Saves the nodes, adj, edges datastructures to .csv files in *python/data/processed/skeleton\_networks*



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

1. Register embryo metadata from ImageJ. We set up a metadata\_df which assigns each embryo an embryo\_ID. This might seem complex but assigning a unique embryo\_ID is much easier for a computer to store and locate save files (e.g. vs long strings such as "*\[stage]\_\[n]\_\[experiment\_date]\_\[drug\_name]\_\[condition]*". The measurement data is already generated from ImageJ, so *algorithms/database.py* just handles managing the embryo\_ID system to stop duplicate data etc.
2. Run the skeleton model and save csv's via *form\_networks\_all*.
3. Gather the summary statistics per embryo (e.g. number of components, number of cycles) and save in summary.csv.



###### **3. Visualisation**

skeleton\_visualisation.iypnb and algorithms/visualisation.py



Displays the skeleton network for one embryo per stage, e.g. for verifying the preprocessing and parameter fitting.

Later code uses the functions *image\_plot* and *nodes\_plot* to display zoomed regions e.g. for use in figures.

Both functions are designed to display a selected region, specified by *size, x\_min, y\_min*.

Useful for general testing.



###### **4. Analysis**



The core analysis is displayed in ***skeleton\_analysis\_results.ipynb***, generated in *algorithms/analysis.py*

The code works as follows: use *database.get\_embryo\_IDs\_from\_drug()*, which returns a list of embryo\_IDs based on the drug condition provided (leave blank for normal dataset). Then call *analysis.plot\_feature\_by\_stage()* with a specified feature and the list of embryo\_IDs.



The plots are automatically saved as .svg and .png files if save=True, in the folder *python/skeleton/results/skeleton\_analysis\_results/main*

It is recommended to run with save=False to check if the data looks reasonable, then set save=True, to avoid overwriting data with faulty graphs.



**Analysis metrics**



Embryo area is defined by the ellipse drawn by the user in preprocessing.

Embryo width is defined by the minimum and maximum x coordinate of nodes.



|Network Property / name in analysis.py|Biological Property (graph title)|Meaning and notes|Unit|
|-|-|-|-|
|Number of Nodes|Number of Blood Island Clusters|Each node approximately represents a blood island region|Whole number|
|Mean Edge Length|Average Distance between Blood Island Clusters|an edge represents a link between blood island regions|Microns|
|Mean Node Weight|Average Blood Island Cluster Size|Maybe "Blood Island Cluster Width" is a better label. The node weight represents the blood island thickness before skeletonisation, so it's a measure of how "large" the node is.|Microns|
|Number of Isolated Nodes|Number of Isolated Blood Island Clusters|Isolated nodes: have 0 edges so are entirely separated from the network.|Whole number|
|Average Degree of Non-Isolated Nodes|Average Connectivity of Non-Isolated Nodes|Degree: the number of edges a node has. It is a measure of connectivity. So we find the average connectivity of all nodes (excluding the ones where connectivity is zero).|Number|
|Average Shortest Path||Not actually a useful metric because connectivity is low. Would be more useful when a mega component is forming.<br /><br />Take the largest component (as paths between different components do not exist), then calculate the shortest path between all pairs of two nodes and find the average|Microns|
|Number of Basis Cycles|Number of Enclosed Holes|Cycle: a loop that starts and ends in the same place.<br /><br />The basis cycles are the set of linearly independent cycles - e.g. because two cycles can be joined to make a third cycle, we don't want to overcount.<br />See networkX documentation|Whole number|
|Number of Components||A component is a set of blood islands that are all connected to each other via edges.|Whole number|
|Average Clustering||The average clustering coefficient of each node, which measures how well its neighbours are connected or how "clustered" the node is.<br /><br />See networkX documentation<br /><br />In practice the numbers are so low that this is not a useful metric.|Number|
|Number of Components, Excluding Isolated Nodes||Exclude the isolated nodes (which are their own component, so it can bloat up the number of components a lot).|Whole number|
|Number of Isolated Nodes / Nodes|Proportion of Isolated Blood Island Clusters|Of all blood island clusters, what proportion are isolated (no connections)|Number|
|Mean Edge Length / Width|Mean Edge Length, Relative to Embryo Width|Not a very useful metric.<br />Wanted to check if the edges were only growing in length due to the whole embryo growing in size (e.g. edges stretch rather than grow)|Number between 0 and 1|
|Number of Nodes / Area|Number of Blood Island Clusters per Square Micron|Density of nodes (normalised to the area).|Number per square micron|
|Basis Cycles / Area|Number of Enclosed Holes per Square Micron|Density of holes (normalised to the area).|Number per square micron|
|Isolated Nodes / Area|Isolated Nodes per Square Micron|Density of isolated nodes (normalised to the area).|Number per square micron|
|Number of Components / Area|Number of Components, Excluding Isolated Nodes per Square Micron|Density of components (normalised to the area).|Number per square micron|
|Mean Edge Thickness||For each pixel in the skeleton image forming the edge, find the thickness value of that pixel from the distance map. Then take average.|Microns|





Additional analysis files:



Area\_analysis\_results.ipynb: contains plots for the entire embryo size, blood island size and component distribution.

network\_type\_analysis\_results.ipynb: contains plots for the degree distribution and clustering coefficient per embryo.





**spatial\_analysis\_grid.ipynb:** Splits the embryo into grid regions to compare spatial properties. The code is not very robust at the moment. You can adjust the n\_rows and n\_cols to adjust the number of rows and columns in the grid but I think plotting will only work for n=2 (so left/right, anterior/posterior).



**spatial\_analysis\_distance.iypnb:** Instead of using a grid to determine spatial properties, determine how close each blood island is to the centre of the embryo and use this to parameterise factors like node size. Uses the ellipse properties which are fitted by the user in ImageJ.



The distance parameter is based on the following:

Calculate the radius of the ellipse that a given coordinate would lie on, given a centre point, and a and b.

Since the original radius is always 1: (x-c1)\*\*2/a\*\*2 + (y-c2)\*\*2/b\*\*2=1, this tells us, in a radial sense, how "far" the point is from the centre of the embryo, on a scale from 0 (at the centre) to 1 (on the edge of the ellipse).





###### **Deletion, Maintenance, Analysis**

You do not need to delete or rerun anything to add more embryos to the dataset. Just run the macro, then run\_skeleton\_model.ipynb. Preexisting files will be skipped to avoid redundant processing.



If you want to rerun the model, delete the .csv files from data/processed/skeleton\_networks, delete metadata.csv and summary.csv.

If you want to rerun the preprocessing and the model, delete the above, AND delete the files in python/data/raw/main (or drugs), and data/imagej/imageJ\_metadata.csv





Explanation of coding implementation

* When appending to dataframes in a loop, it is faster to append data as a dictionary to a list, then convert this list to a dataframe at the very end (as .loc in a loop is quite slow)



**How to add more analysis**

