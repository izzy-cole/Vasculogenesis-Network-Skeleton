//Do not show processing windows
setBatchMode(true);

//specify stages and n
stages = newArray(3,4,5,6,7,8,9,10,11,12,13);
n_s = newArray("1", "2", "3", "4", "5");

//configure the main and save path
main_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/imageJ/raw/main/";
save_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/raw/main/";


//should read in a "hh9_n1 BC.tif" file where the background is clearly black and the blood islands are white (does not need to be a binary/thresholded image)
//each image should include the measurements in microns

//spatial resolution: number of pixels per micron
//would be nice if this could read from a central config.py file
pix_micron_ratio = 0.25;

//gaussian blur parameter in microns
blur_in_microns = 10;

//minimum particle size in microns squared
min_particle_size=200;


for (s=0;s<stages.length;s++){
	stage = stages[s];
	for (n = 1; n <= n_s.length; n++) {
		file_name = "hh"+stage+"_n"+n+" BC.tif";
		
		if (!File.exists(main_path+file_name)) {
			print("File n"+n+" hh"+stage +" does not exist, skipping");
			continue;
		}
		
		//open image
		//print(main_path+file_name);
		open(main_path+file_name);
		
	
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
	    rename("scaled.tif");
		
		//gaussian blur
		run("Duplicate...", "title=blur_target");
		selectImage("blur_target");
		run("Gaussian Blur...", "sigma="+blur_in_microns+ " scaled"); //"scaled" means it works in the microns unit
		
		//particles and fill them
		run("Apply LUT");
		run("Auto Threshold", "method=Otsu white");
		run("Analyze Particles...", "size="+min_particle_size+"-Infinity show=Masks display clear add composite");
		
		//fills particles
		count = roiManager("count");
		array = Array.getSequence(count);
		roiManager("Select", array);
		roiManager("Fill");
		rename("particles.tif");
		
		//skeletonise
		run("Duplicate...", "title=skeleton_target");
		run("Skeletonize (2D/3D)");
		run("Invert LUT");
		
		//saves the main skeleton files to both paths
		saveAs("Tiff", save_path+"hh"+stage+"_n"+n+" skeleton.tif");
		
		
		//distance map generation
		selectImage("particles.tif");
		run("Convert to Mask");
		run("Geometry to Distance Map", "threshold=128");
		run("Grays");
		
		
		//save distance maps
		saveAs("Tiff", save_path+"hh"+stage+"_n"+n+" distmap.tif");
		
		//OPTIONAL: just save the scaled image to the python folder - not needed for Python but makes it easy to check for mistakes.
		selectImage("scaled.tif");
		saveAs("Jpeg", save_path+"hh"+stage+"_n"+n+" plain_scaled.jpg");
		
		//close stuff
		roiManager("reset");
	    run("Clear Results");
	    close("*");
    
	}
}

print("Done!")