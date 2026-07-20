
stage=12;
n=1;


main_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/imageJ/raw/live_imaging/";
save_path = "C:/Users/isabe/Documents/work/systems bio/modelling vasculogenesis/imageJ/raw/live_imaging/hh"+stage+"_n"+n+"/";


file_name = "hh"+stage+"_n"+n+" BC.tif";
setBackgroundColor(0, 0, 0);
setBatchMode(false);

if (!File.exists(main_path+file_name)) {
	print("File "+ file_name +" does not exist");
} else{
	open(main_path+file_name);
	
	// Force Timesteps (Frames) to become Slices
	Stack.getDimensions(width, height, channels, slices, frames);
	if (frames > 1 && slices == 1) {
    	run("Properties...", "channels=" + channels + " slices=" + frames + " frames=1");
	    print("Reconfigured hyperstack: Converted " + frames + " frames into slices.");
	}

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
	setBatchMode(true);
	
	//Split and save individual slices as images, with the correct names
	rename("stack");
	for (i=1; i<=nSlices;i++){
		selectImage("stack");
		setSlice(i);
		run("Duplicate...", "title=temp_slice");
		slice_name = ""+i;
		if (lengthOf(slice_name) == 1) {
	        slice_name = "00" + slice_name; //Set up 0 padding (3 digits total)
	    } else if (lengthOf(slice_name) == 2) {
	        slice_name = "0" + slice_name;
	    }
	    file_name = "hh" + stage + "_n" + n + "_s" + slice_name + " BC.tif";
	    rename(file_name);
	    saveAs("Tiff", save_path + file_name);
	    close();
	}
	close("*");
}
			

