//specify stages and n
drug_name = "mmp hh8+24hr";
conditions = newArray("control nuclei", "10um nuclei","20um nuclei");

drug_name = "mmp brendan2";
conditions = newArray("Control","10um", "20um","30um");

//should read in a "hh9BC.tif" file where the background is clearly black and the blood islands are white (does not need to be a binary/thresholded image)
//each image should include the measurements in microns
//right now the file structure is "hh9/1/skeleton" so that each embryo (n=1,2,3,...) is kept in a separate folder. The code only runs for 1 value of n
//This could easily be adapted via a second for loop, or by moving all files into one folder.

//spatial resolution: number of pixels per micron
pix_micron_ratio = 0.25;

//gaussian blur parameter in microns
blur_in_microns = 10;

//minimum particle size in microns squared
min_particle_size=200;


for (i=0;i<conditions.length;i++){
	j=conditions[i];
	
	//configure the main and save path
	main_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/hh_stages_fixed_images/drug_perturbation_set/"+drug_name+"/skeleton/";
	save_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/skeleton/drugs/"+drug_name+"/";
	
	//open image
	print(main_path+j+" BC.tif");
	open(main_path+j+" BC.tif");
	

	getPixelSize(unit, pixelWidth, pixelHeight);
	print("pixel to micron ratio is "+pixelWidth);
	
	// If the image is uncalibrated, ImageJ defaults the unit to "pixels" or "inch"
	if (unit == "pixels" || unit == "inch") {
		// Print a warning to the log, close the image, and skip
		print("  -> ERROR: No micron metadata found for HH" + j + ". Skipping image.");
		close("*");
		continue; 
	}
	
	//remove any hidden ROI selections, if present by accident
	run("Select None");
	//scale to correct ratio
	scale_factor = pixelWidth*pix_micron_ratio;
	run("Scale...", "x="+scale_factor+ " y="+scale_factor+" interpolation=Bilinear average create");
	
	// Force ImageJ to recognize the new standardized physical scale.
    // E.g., if ratio is 0.25, the new pixel width is exactly 4 microns per pixel.
    new_micron_width = 1 / pix_micron_ratio;
    run("Set Scale...", "distance=1 known=" + new_micron_width + " unit=microns");
    rename(j+" scaled.tif");
	
	//gaussian blur
	run("Duplicate...", "title=blur_target");
	selectImage("blur_target");
	run("Gaussian Blur...", "sigma="+blur_in_microns+ " scaled"); //"scaled" means it works in the microns unit
	saveAs("Tiff", main_path+j+" blur.tif");
	
	//particles and fill them
	run("Apply LUT");
	run("Auto Threshold", "method=Otsu white");
	run("Analyze Particles...", "size="+min_particle_size+"-Infinity show=Masks display clear add composite");
	
	//fills particles
	count = roiManager("count");
	array = Array.getSequence(count);
	roiManager("Select", array);
	roiManager("Fill");
	
	saveAs("Tiff", main_path+j+" particles.tif");
	rename(j+" particles.tif");
	
	//skeletonise
	run("Duplicate...", "title=skeleton_target");
	run("Skeletonize (2D/3D)");
	run("Invert LUT");
	
	//saves the main skeleton files to both paths
	saveAs("Tiff", main_path+j+" skeleton.tif");
	saveAs("Tiff", save_path+j+" skeleton.tif");
	
	
	//distance map generation
	selectImage(j+" particles.tif");
	run("Convert to Mask");
	run("Geometry to Distance Map", "threshold=128");
	run("Grays");
	
	
	//save distance maps
	saveAs("Tiff", main_path+j+" distmap.tif");
	saveAs("Tiff", save_path+j+" distmap.tif");
	
	//OPTIONAL: just save the scaled image to the python folder - not needed for Python but makes it easy to check for mistakes.
	selectImage(j+" scaled.tif");
	saveAs("Jpeg", save_path+j+"_plain_scaled.jpg");
	
	//close stuff
	roiManager("reset");
    run("Clear Results");
    close("*");

}