# Vasculogenesis-Network-Skeleton

Custom image processing and network analysis tool designed to quantify network formation and structure of blood islands in chicken embryos.





**Features**

1. **Adaptive image segmentation: uses local Bernsen thresholding to generate high quality blood island segmentation with minimal manual input, adapting to variable image contrast.**

**2. Network model setup and a custom node-merging algorithm to ensure network structures are biologically significant.**

**3. Dataset handling via an embryo\_ID system allows for unambiguous, high-throughput processing of standard and drug experiment datasets.**

**4. Plotting and visualisation code including tracking feature changes through development, spatial grid analysis, and area analysis.**

**5. Under development: support for image stacks, to track network features for live time-lapse imaging.**



**Installation and use**

```bash

git clone \[https://github.com/yourusername/vasculogenesis-modeling.git](https://github.com/yourusername/vasculogenesis-modeling.git)

cd vasculogenesis-modeling

pip install -r requirements.txt

Run the image editing and preprocessing script skeleton.ijm via Fiji/ImageJ

Set up file paths in config.py

Run run\_skeleton\_model.ipynb to initialise the network model, then view analytics via skeleton\_analysis\_results.ipynb

See the full guide.md for detailed information on parameter setup.



