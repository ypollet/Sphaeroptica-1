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

sys.path.append("/home/broot/Numerisation/Sphaeroptica")

from matplotlib import pyplot as plt
import json
import numpy as np
from scripts import converters
import argparse
from pathlib import Path

from scripts import reconstruction

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

    centers = [[],[],[]] #lim x_y_z
    rotations = [[[] for _ in range(3)] for _ in range(3)] # makes a 3D array 3*3*N for each x_ij of rotation matrices

    print(f"Len images = {len(extrinsics)}")
    for image in extrinsics:
        matrix = np.matrix(extrinsics[image]["matrix"])
        rotation = matrix[0:3,0:3]
        trans = matrix[0:3,3]
        C = converters.get_camera_world_coordinates(rotation, trans)
        
        centers[0].append(C.item(0)) # x
        centers[1].append(C.item(1)) # y
        centers[2].append(C.item(2)) # z
        
        for idx, val in np.ndenumerate(rotation):
            rotations[idx[0]][idx[1]].append(val)

        if rotation[0].dot(rotation[1].T) > 1e-6 or rotation[0].dot(rotation[2].T) > 1e-6 or rotation[2].dot(rotation[1].T) > 1e-6 :
            # Simply checks that all the angles of the rot matrix are perpendicular
            print(f"Angles not perpendicular for image {image}")

    # get dimensions of plot
    limits = [[min(i), max(i)] for i in centers]
    dimension = max([i[1] - i[0] for i in limits])


    
    # plot cameras
    ax.scatter(centers[0], centers[1], centers[2], color="blue")
    '''ax.quiver(centers[0], centers[1], centers[2], rotations[0][0], rotations[0][1], rotations[0][2], length=dimension*0.1, color="red")
    ax.quiver(centers[0], centers[1], centers[2], rotations[1][0], rotations[1][1], rotations[1][2], length=dimension*0.1, color="blue")
    ax.quiver(centers[0], centers[1], centers[2], rotations[2][0], rotations[2][1], rotations[2][2], length=dimension*0.1, color="green")'''
    # plot center
    radius, center = reconstruction.sphereFit(centers[0], centers[1], centers[2])
    print(center)
    ax.scatter(center.item(0), center.item(1), center.item(2), color="black", label='center')
    ray_x = np.array([1,0,0]).T
    ax.quiver(center.item(0), center.item(1), center.item(2), ray_x.item(0), ray_x.item(1), ray_x.item(2), length=dimension*0.15, color="red")
    ray_y = np.array([0,1,0]).T
    ax.quiver(center.item(0), center.item(1), center.item(2), ray_y.item(0), ray_y.item(1), ray_y.item(2), length=dimension*0.15, color="blue")
    ray_z = np.array([0,0,1]).T
    ax.quiver(center.item(0), center.item(1), center.item(2), ray_z.item(0), ray_z.item(1), ray_z.item(2), length=dimension*0.15, color="green")

    # Plot Sphere Grid
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x=np.cos(u)*np.sin(v)*radius
    y=np.sin(u)*np.sin(v)*radius
    z=np.cos(v)*radius
    x = x + center[0]
    y = y + center[1]
    z = z + center[2]

    ax.plot_surface(x, y, z, color="black", alpha=0.1)

    avg = [np.average(i) for i in limits]
    ax.set_xlim3d(avg[0]-(dimension/2*1.2), avg[0]+(dimension/2*1.2))
    ax.set_ylim3d(avg[1]-(dimension/2*1.2), avg[1]+(dimension/2*1.2))
    ax.set_zlim3d(avg[2]-(dimension/2*1.2), avg[2]+(dimension/2*1.2))


    ax.set_aspect("equal")

    plt.legend(loc="upper right")
    plt.show()

    calib_file.close()