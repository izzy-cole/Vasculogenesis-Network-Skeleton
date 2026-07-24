
stage=11;
n=1;

record_metadata=true;

live_name = "1";
main_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/imageJ/raw/live_imaging/";
save_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/raw/live_imaging/hh"+stage+"_n"+n+"/";
csv_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/imagej/imageJ_metadata_live" + live_name + ".csv";

//spatial resolution: number of pixels per micron
pix_micron_ratio = 0.25;

//gaussian blur parameter in microns
blur_in_microns = 7.5;

//minimum particle size in microns squared
min_particle_size=900;

//Radius for local thresholding in microns 
local_threshold_radius=30;


file_name = "hh"+stage+"_n"+n+" BC.tif";
setBackgroundColor(0, 0, 0);
setBatchMode(false);

if (!File.exists(main_path+file_name)) {
	print("File "+ file_name +" does not exist");
} else{
	open(main_path+file_name);
	run("8-bit");
	
	// Force Timesteps (Frames) to become Slices
	Stack.getDimensions(width, height, channels, slices, frames);
	if (frames > 1 && slices == 1) {
    	run("Properties...", "channels=" + channels + " slices=" + frames + " frames=1");
	    print("Reconfigured hyperstack: Converted " + frames + " frames into slices.");
	}
	
	//Rescale to correct ratio
	getPixelSize(unit, pixelWidth, pixelHeight);
	print("pixel to micron ratio is "+pixelWidth);
	
	// If the image is uncalibrated, ImageJ defaults the unit to "pixels" or "inch"
	if (unit == "pixels" || unit == "inch") {
		// Print a warning to the log, close the image, and skip
		print("  -> ERROR: No micron metadata found for " + file_name +". Skipping image.");
		close("*");
	}
	
	//remove any hidden ROI selections, if present by accident
	run("Select None");
	//scale to correct ratio
	scale_factor = pixelWidth*pix_micron_ratio;
	run("Scale...", "x="+scale_factor+ " y="+scale_factor+" interpolation=Bilinear average create process");
	
	// Force ImageJ to recognize the new standardized physical scale.
    // E.g., if ratio is 0.25, the new pixel width is exactly 4 microns per pixel.
    new_micron_width = 1 / pix_micron_ratio;
    run("Set Scale...", "distance=1 known=" + new_micron_width + " unit=microns to=[all]");
    rename("scaled.tif");
    
    w = getWidth();
    h = getHeight();

	//metadata annotations
	
	//Rotate the embryo based on line provided by user
    run("Clear Results");
    setTool("line");
	waitForUser("Manual Axis", "Draw a line representing the centre of the embryo, from posterior to anterior. \nImage: " + file_name);
	run("Measure");
	// Grab the angle from the last row of the Results table
	angle = getResult("Angle", nResults - 1);
	new_angle = angle - 90;
	run("Rotate... ", "angle="+new_angle+" grid=0 interpolation=Bilinear stack");
	
	if (record_metadata){	
		//Locate top of embryo
		run("Clear Results");
		setTool("point");
		waitForUser("Locate anterior", "Draw a point representing the top anterior of the extraembryonic region \nImage: " + file_name);
		run("Measure");
		ant_x = getResult("X", nResults - 1);
	    ant_y = getResult("Y", nResults - 1);
		
		//Fit ellipse
		run("Clear Results");
		setTool("oval");
		waitForUser("Fit ellipse", "Draw an ellipse fitting the blood islands \nImage: " + file_name);
		run("Measure");
		ell_x = getResult("X", nResults - 1);
		ell_y = getResult("Y", nResults - 1);
		ell_w = getResult("Width", nResults - 1);
		ell_h = getResult("Height", nResults - 1);
		
	}
	
    //Set contrast
	run("Select None");	
	run("Brightness/Contrast...");
	waitForUser("Set min/max", "Set min/max in BC panel, then press OK when done.");
	run("Apply LUT","stack");
	
	
	low_contrast = getBoolean("Low contrast mode? \n (recommended: try first without, if image is bad, repeat with low contrast mode)");
	if (low_contrast){
		thin_vessel = getBoolean("Otsu mode? \n (recommended: for stages HH12 and HH13)");
	} else{
		thin_vessel=false;
	}
	
	
	//Manual deletion of regions across all frames
	continuing = true;
	while (continuing){
		setTool("freehand");
		waitForUser("Delete Noise", "Draw a region to delete across the entire stack, then press OK.");
		// The "stack" argument clears the selection on ALL slices
		if (selectionType() != -1) {
	    	run("Clear", "stack");
		}
	    // Deselect so the user can see the cleared region clearly
	    run("Select None");
	        
	    //Ask the user if they want to delete more or stop
	    continuing = getBoolean("Delete another region?");
	    	
	}
	rename("stack");

	
	//save metadata and files slice by slice
	setBatchMode(true);
	if (!File.exists(csv_path)) {
	    File.append("Stage,n,Condition,Angle,Width,Height,Anterior_X,Anterior_Y,Ellipse_X,Ellipse_Y,Ellipse_W,Ellipse_H", csv_path);
	}
	
	//Split and save individual slices as images, with the correct names
	
	total_slices = nSlices;

	for (i=1; i<=total_slices;i++){
		
		//set up slice name
		slice_name = ""+i;
		if (lengthOf(slice_name) == 1) {
	        slice_name = "00" + slice_name; //Set up 0 padding (3 digits total)
	    } else if (lengthOf(slice_name) == 2) {
	        slice_name = "0" + slice_name;
	    }
		
	
		// Append the metadata for this embryo
		cond_label = "s" + slice_name;
		if (record_metadata){
			File.append(stage + "," + n + "," +cond_label+ ","+ new_angle + "," + w + "," + h + ","+ant_x+","+ant_y+","+ell_x+","+ell_y+","+ell_w+","+ell_h, csv_path);
		}
		
	    selectImage("stack");
	    setSlice(i);
	    run("Duplicate...", "title=slice");
	    
	    run("Duplicate...", "title=slice");
	    saveAs("Jpeg", save_path+"hh"+stage+"_n"+n+"_"+cond_label+" plain_scaled.jpg");
	    close();
	    
	    run("Select None");
	    selectImage("slice");
		//gaussian blur
		run("Duplicate...", "title=blur_target");
		run("Gaussian Blur...", "sigma="+blur_in_microns+ " scaled"); //"scaled" means it works in the microns unit
	    
		//Local thresholding section
		if (!low_contrast){
			//Get dark and light using mean and stddev (to prevent outlier pixels affecting the range)
			getStatistics(area, mean, min, max, stdDev);
			dark = mean - (2.5 * stdDev);
			if (dark < 0) dark = 0; // prevent negative values
	
			light = mean + (2.5 * stdDev);
			if (light > 255) light = 255; //  prevent overflow
		
			//Arbitrary scaling based on trial and errro
			ref_range = 208-34;
			scaled_contrast = ((light-dark)/ref_range)*150;
			print("Scaled contrast is: "+scaled_contrast+", local threshold radius is: " + local_threshold_radius);
			run("Auto Local Threshold", "method=Bernsen radius="+local_threshold_radius+" parameter_1="+scaled_contrast+" parameter_2=0 white");
		
		} else{
			if (!thin_vessel){
			run("Auto Local Threshold", "method=Bernsen radius="+local_threshold_radius+" parameter_1=0 parameter_2=0 white");
			}
			else{
				run("Auto Local Threshold", "method=Otsu radius="+local_threshold_radius+" parameter_1=0 parameter_2=0 white");
			}
		}
		
		//fill gaps generated by local threshold
		run("Remove Outliers...", "radius=4 threshold=50 which=Dark");
		
		//particles and fill them
		run("Analyze Particles...", "size="+min_particle_size+"-Infinity show=Masks display clear add composite");
		
		//fills particles
		count = roiManager("count");
		array = Array.getSequence(count);
		roiManager("Select", array);
		roiManager("Fill");
		rename("particles.tif");
		run("Invert LUT");

	
		//skeletonise
		run("Duplicate...", "title=skeleton_target");
		run("Skeletonize (2D/3D)");
		run("Invert LUT");
		rename("skeleton");
		saveAs("Tiff", save_path+"hh"+stage+"_n"+n+"_"+cond_label+" skeleton.tif");
		close();
	
		
		//distance map generation
		selectImage("particles.tif");
		run("Duplicate...", "title=distmap_target");
		run("Convert to Mask");
		run("Geometry to Distance Map", "threshold=128");
		run("Grays");
		saveAs("Tiff", save_path+"hh"+stage+"_n"+n+"_"+cond_label+" distmap.tif");
		close();
		
		//save particles
		selectImage("particles.tif");
		saveAs("Tiff", save_path+"hh"+stage+"_n"+n+"_"+cond_label+" particles.tif");
		close();

		roiManager("reset");
		run("Clear Results");
		close("slice");
		close("particles");
		close("blur_target");
		close("distmap_target");
	}
	close("*");
}
			

