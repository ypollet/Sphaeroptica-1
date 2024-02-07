# Sphaeroptica - 3D Viewer on calibrated

# Copyright (C) 2023 Yann Pollet, Royal Belgian Institute of Natural Sciences

#

# This program is free software: you can redistribute it and/or

# modify it under the terms of the GNU General Public License as

# published by the Free Software Foundation, either version 3 of the

# License, or (at your option) any later version.

# 

# This program is distributed in the hope that it will be useful, but

# WITHOUT ANY WARRANTY; without even the implied warranty of

# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU

# General Public License for more details.

#

# You should have received a copy of the GNU General Public License

# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
 
# setting path
print(__file__)
sys.path.append(os.path.realpath(f"{__file__}/../.."))


from matplotlib import pyplot as plt
import json
import numpy as np
from scripts import converters
import os
import argparse
from pathlib import Path

if __name__ == '__main__':
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True,
                    help="path to input OPK File")
    args = vars(ap.parse_args())

    calib_file = open(Path(args["input"]))
    extrinsics = json.load(calib_file)


    fig = plt.figure()
    ax = plt.axes(projection='3d')


    dist = 0
    center = np.array([[0.0],[0.0],[0.0]])

    proj_points = []
    for image in extrinsics:
        matrix = np.matrix(extrinsics[image]["matrix"])
        rotation = matrix[0:3,0:3]
        trans = matrix[0:3,3]
        C = converters.get_camera_world_coordinates(rotation, trans)
        if image.startswith('_x_00200_'):
            if image == '_x_00200_y_00000_.jpg':
                ax.scatter(C.item(0), C.item(1), C.item(2), color="green", label="frontal view")
            else:
                ax.scatter(C.item(0), C.item(1), C.item(2), color="red")
            
        else:
            ax.scatter(C.item(0), C.item(1), C.item(2), color="blue")
        
        ray_x = (rotation[0])
        ax.quiver(C.item(0), C.item(1), C.item(2), ray_x.item(0), ray_x.item(1), ray_x.item(2), length=0.35, color="red")
        ray_y = (rotation[1])
        ax.quiver(C.item(0), C.item(1), C.item(2), ray_y.item(0), ray_y.item(1), ray_y.item(2), length=0.35, color="blue")
        ray_z = (rotation[2])
        ax.quiver(C.item(0), C.item(1), C.item(2), ray_z.item(0), ray_z.item(1), ray_z.item(2), length=0.35, color="green")
        if ray_x.dot(ray_y.T) > 1e-6 or ray_x.dot(ray_z.T) > 1e-6 or ray_z.dot(ray_y.T) > 1e-6 :
            print(f"Angles not perpendicular for image {image}")
        center += C
    center = center/len(extrinsics)
    print(center)
    ax.scatter(center.item(0), center.item(1), center.item(2), color="black", label='center')
    ray_x = np.array([1,0,0]).T
    ax.quiver(center.item(0), center.item(1), center.item(2), ray_x.item(0), ray_x.item(1), ray_x.item(2), length=0.35, color="red")
    ray_y = np.array([0,1,0]).T
    ax.quiver(center.item(0), center.item(1), center.item(2), ray_y.item(0), ray_y.item(1), ray_y.item(2), length=0.35, color="blue")
    ray_z = np.array([0,0,1]).T
    ax.quiver(center.item(0), center.item(1), center.item(2), ray_z.item(0), ray_z.item(1), ray_z.item(2), length=0.35, color="green")

    '''
    ax.set_xlim3d(-0.3, 0.3)
    ax.set_ylim3d(-0.3, 0.3)
    ax.set_zlim3d(-0.22, 0.22)'''
    plt.legend(loc="upper right")
    plt.show()

    calib_file.close()