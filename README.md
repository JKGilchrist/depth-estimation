# Depth-estimation

This module generates estimated depth maps for stereo pairs of featureless regions


## Install
If working with anaconda, then from the root directory:
```
conda env create --file environment.yml
conda activate image-processing

```
Otherwise, if python 3 is installed, pip can be used to ensure the required packages are available. From the root directory, run
```
pip install -r requirements.txt
```

## Files
The core functional files are collection.py, image.py, shape.py, edge.py, segment.py. They each contain a class of the same name. They logically follow this order and encapsulate each other, so collection creates three image objects for the left, center and right images. Each image object creates a number of shape objects. Shape objects create edge objects. Edge objects create segment objects. helper.py contains assisting functions used by these various classes.

This design aids in splitting up all the information and processes necessary to perform the desired function and logically groups it to ease comprehension. Each ought to be well-commented enough to generally understand what each part is doing. 

The only one intended to be accessed to retrieve depth maps is collection.py as it orchestrates the entire process. 


## Usage
Both main.py and auto_gen.py are designed to access collection and to have it create depth maps. They require the initial images to be stored within a directory in assets/ , and each with three further subdirectories, cameraLeft/, cameraCenter/, and cameraRight/ . They save their results to saves/ with the generated images being stored in saves/generated/ . All .img files are object-files generated during this process to reduce the workload needed the next time the same process is executed.

### _Main_
main.py is for individual depth map generation. There are four arguments able to be passed to specify details to the execution. 
1. The directory name desired from within assets/ .
2. The numerical index (starting at 0) of the specific image desired within the innermost subdirectories
3. The number representing which image should the depth map visual be based on (0 for left, 1 for center, 2 for right)
4. Should the resulting depth image be saved
5. Should the resulting depth image be displayed

While it can take up to these four arguments, no arguments is also possible. Then, the directory within assets/ is randomly selected, as is the index of the image set, and which image is used to generate the depth map visual. It will save and display the results. Partial arguments is also fine, so long as order is maintained.

Example: To display on the left image but not save occluded_road's first image set 
```
python main.py occluded_road 0 0 False True
```
_note: the last argument, True, is redundant in this case_  
&nbsp;  
Example: Any road_no_occlusion image set, any image used to create the depth map visual (automatically will save and display)
```
python main.py road_no_occlusion
```
&nbsp;  

Example: Anything (automatically will save and display)
```
python main.py
```
&nbsp;  

The value of having it execute a certain image when its depth image has already been generated is that it will quickly pull it up in the viewer and unlike the static image one can view the individual pixel values the mouse hovers over in the top-right corner. 

&nbsp;  

### _Auto_gen_
Alternatively, auto_gen.py is intended for the automated creation of all depth map images.
```
python auto_gen.py
```
By simply executing it, it will determine the depth map image all image sets and save them all. The terminal output is saved to a txt file stored in saves/logs. It does not display the results, as that would greatly heed the process of creating all of the results.

Alternatively, it can take two arguments. 
1. Specifies a directory within assets/ to use rather than executing for all of them, similar to the first argument for main.py
2. Specifies the image to be used as the basis for the depth map visual, similar to the third argument for main.py (0-2 for left, center, and right)

Example: All depth images
```
python auto_gen.py
```
&nbsp;  
Example: All Shape_based_stereoPairs depth images using the right image
```
python auto_gen.py Shape_based_stereoPairs 2
```
&nbsp;  

For both, if an existing depth map exists, it will not be redone even if the image expected to be used is different. To do so, remove both the .jpg and .img and re-run.

## How it works
&nbsp;  
### _Initialization_

Upon creation of an instance of collection, it first intantiates the left image's Image intance. The shape colours are determined and then each shape is instantiated. The bounding box of the given shape is determined as well as its left and right edges, and their segments. 

Collection uses the colours determined by the left Image to speed up the other two image's instantiations. 

After everything has been created, the segments of each edge, of each shape, in each image must be assigned. First this process requires determining the displacement of edges, which is then used to determine which shape owns and doesn't own which segment. 

Generally at this stage all but a few stragglers are assigned. The remaining are due to shapes having few edges, and the only one it could own is shared with the ground or sky shape, and thus difficult to tell which owns it. Using additional information about the shapes ownership is assigned. Finally, it checks to see if any shapes are the ground or sky, as their depths are not calculated.

At this stage, the image objects are saved.

### _Depth calculation_
Then, using this information about the edges of a shape, its depth can be more accurately calculated. Only edges it owns are used to determine its depth. So if it only has its right side, only the right edge is used. Alternatively if both are owned, the midpoint is used. 

However, if the shape is determined to have a varying depth, then its depth can alternatively be calculated using the change of slope between the images. 

Finally, once all depth values are found, a modified version of the original image is created with its shape colours replaced with their determined depth values, the sky is replaced with pure black, and the ground with pure white. This image is then possibly saved and possibly displayed. Which image is used to re-colour for the depth map depends on either a given argument or random selection.
