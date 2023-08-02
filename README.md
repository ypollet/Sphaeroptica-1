# Sphaeroptica

Sphaeroptica is an open-source viewer based on photogrammetry that allows to view 3D objects without needing to compute a 3D model.

## Requirements

Here is the list of the requirements needed to run Sphaeropica :

* python >= 3.8
* numpy
* scipy
* pyqt 6
* imutils
* opencv-contrib-python

## Quick Start Guide

Start the application with :

```python3 app.py```

Sphaeroptica has two functionalities : 
* calibration with Zhang pattern
* view and measurements of an object
### Calibration

Select the directory that contains all the images needed for the calibration process.

Put the number of points that can be found in the pattern, first the lenght, then the width.   
It is usually the number of squares + 1.
For the test_calib directory in data, it will be 9*6.

Add the length and width of the squares

And then press `Calibrate Scanner` to launch the calibration process.

Finally, save the calibration data in a json form if needed.

### View and measurements

Import the calibration.json file in data/geonemus-geoffroyii. It contains all the data needed for the viewing of the images in the same directory : 
* intrinsic calibration
* extrinsic
* distortion coefficients
* a directory of thumbnails for the virtual camera

![Screen of the application](./images/Sphaeroptica.png)

On the left, we have the virtual camera.

On the right, we have :
* Quick buttons to get to a desired view
* A list of desired 3D points
* A distance calculator between two 3D points

Click on values under to display the nearest image to be able to place landmark for the triangulation of points

![Screen of the application](./images/show_picture.png)

Place landmarks on the points that you can see on the image.

When two or more landmarks have been placed for the same point, Sphaeroptica will start a triangulation process to compute the 3D coordinates of this point.

## Credits

Icons from Fugue Icon Set — Yusuke Kamiyamane : https://p.yusukekamiyamane.com/
