//Do not show processing windows
batchMode = true;
setBatchMode(batchMode);

//specify stages and n
stages = newArray(3,4,5,6,7,8,9,10,11,12,13);
n_s = newArray("1", "2", "3", "4", "5");
conditions = newArray("","_10um","_20um","_30um","_40um","_control"); //empty string allows for no conditions in non-drug case

//configure the main and save path (comment/uncomment)
//Todo: set this up with a dialogue box.
//Default:
main_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/imageJ/raw/main/";
save_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/raw/main/";
csv_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/temp/imageJ_metadata.csv";

//Drugs:
date = "19072024";
drug_name="MMP";
main_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/imageJ/raw/drugs/"+date+"_"+drug_name+"/";
save_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/raw/drugs/"+date+"_"+drug_name+"/";
csv_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/python/data/temp/"+date+"_"+drug_name+"_imageJ_metadata.csv";

//should read in a "hh9_n1 BC.tif" file where the background is clearly black and the blood islands are white (does not need to be a binary/thresholded image)
//each image should include the measurements in microns

//spatial resolution: number of pixels per micron
//would be nice if this could read from a central config.py file
pix_micron_ratio = 0.25;

//gaussian blur parameter in microns
blur_in_microns = 10;

//minimum particle size in microns squared
min_particle_size=200;

//Change to a while loop??
for (s=0;s<stages.length;s++){
	stage = stages[s];
	for (n = 1; n <= n_s.length; n++) {
		for (c = 0; c< conditions.length; c++) {
			cond = conditions[c];
			file_name = "hh"+stage+"_n"+n+cond+" BC.tif";
			
			//Skip nonexistent files (different amount of n)
			if (!File.exists(main_path+file_name)) {
				print("File "+ file_name +" does not exist, skipping");
				continue;
			}
			
			// ALREADY PROCESSED CHECK
	        final_output = save_path+"hh"+stage+"_n"+n+cond+" distmap.tif";
	        if (File.exists(final_output)) {
	            print("Skipping: " + file_name + " (Already processed)");
	            continue; // Jump to the next embryo
	        }
			
			//open image
			//print(main_path+file_name);
			open(main_path+file_name);
			
		
			getPixelSize(unit, pixelWidth, pixelHeight);
			print("pixel to micron ratio is "+pixelWidth);
			
			// If the image is uncalibrated, ImageJ defaults the unit to "pixels" or "inch"
			if (unit == "pixels" || unit == "inch") {
				// Print a warning to the log, close the image, and skip
				print("  -> ERROR: No micron metadata found for " + file_name +". Skipping image.");
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
		    
		    setBatchMode(false);
		    // Get image dimensions
			w = getWidth();
			h = getHeight();
		    
		    //Rotate the embryo based on line provided by user
		    run("Clear Results");
		    setTool("line");
			waitForUser("Manual Axis", "Draw a line representing the centre of the embryo, from posterior to anterior. \nImage: " + file_name);
			run("Measure");
			// Grab the angle from the last row of the Results table
			angle = getResult("Angle", nResults - 1);
			new_angle = angle - 90;
			run("Rotate... ", "angle="+new_angle+" grid=0 interpolation=Bilinear");
			
			
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
			
			if (!File.exists(csv_path)) {
			    File.append("Stage,n,Condition,Angle,Width,Height,Anterior_X,Anterior_Y,Ellipse_X,Ellipse_Y,Ellipse_W,Ellipse_H", csv_path);
			}
			
			// Append the data for this embryo
			if (cond.length()>0){
				cond2 = substring(cond,1,cond.length());
			} else{
				cond2 = cond;
			}
			File.append(stage + "," + n + "," +cond2+ ","+ new_angle + "," + w + "," + h + ","+ant_x+","+ant_y+","+ell_x+","+ell_y+","+ell_w+","+ell_h, csv_path);
			
			
		    setBatchMode(batchMode);
			
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
			saveAs("Tiff", save_path+"hh"+stage+"_n"+n+cond+" skeleton.tif");
			
			
			//distance map generation
			selectImage("particles.tif");
			run("Convert to Mask");
			run("Geometry to Distance Map", "threshold=128");
			run("Grays");
			
			
			//save distance maps
			saveAs("Tiff", save_path+"hh"+stage+"_n"+n+cond+" distmap.tif");
			
			//OPTIONAL: just save the scaled image to the python folder - not needed for Python but makes it easy to check for mistakes.
			selectImage("scaled.tif");
			saveAs("Jpeg", save_path+"hh"+stage+"_n"+n+cond+" plain_scaled.jpg");
			
			//close stuff
			roiManager("reset");
		    run("Clear Results");
		    close("*");
		}
	}
}

print("Done!")