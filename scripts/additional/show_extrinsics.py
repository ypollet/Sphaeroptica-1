import sys
import os
 
# setting path
print(__file__)
sys.path.append(os.path.realpath(f"{__file__}/../.."))


from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import numpy as np
from scripts import helpers, reconstruction
import os
import argparse
from pathlib import Path

if __name__ == '__main__':

    #extrinsic_file = open(f"{os.path.expanduser('~')}/Numerisation/Sphaeroptica/lysandra_bellargus/jpegs/ext.json")
    #extrinsic_file = open(f"{os.path.expanduser('~')}/Numerisation/Sphaeroptica/Sphaeroptica/data/geonemus-geoffroyii/extrinsics.json")
    #extrinsic_file = open(f"{os.path.expanduser('~')}/Numerisation/Sphaeroptica/lysandra_bellargus/extrinsics.json")
    
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
        print(image)
        matrix = np.matrix(extrinsics[image]["matrix"])
        rotation = matrix[0:3,0:3]
        trans = matrix[0:3,3]

        C = helpers.get_camera_world_coordinates(rotation, trans)
        print(C)
        ax.scatter(C.item(0), C.item(1), C.item(2), color="blue")

        ray_x = (rotation[0]).T
        ax.quiver(C.item(0), C.item(1), C.item(2), ray_x.item(0), ray_x.item(1), ray_x.item(2), length=0.03, color="red")
        ray_y = (rotation[1]).T
        ax.quiver(C.item(0), C.item(1), C.item(2), ray_y.item(0), ray_y.item(1), ray_y.item(2), length=0.03, color="blue")
        ray_z = (rotation[2]).T
        ax.quiver(C.item(0), C.item(1), C.item(2), ray_z.item(0), ray_z.item(1), ray_z.item(2), length=0.03, color="green")

        center += C
    center = center/len(extrinsics)
    print(center)
    ax.scatter(center.item(0), center.item(1), center.item(2), color="black", label='center')

    '''
    ax.set_xlim3d(-0.3, 0.3)
    ax.set_ylim3d(-0.3, 0.3)
    ax.set_zlim3d(-0.22, 0.22)'''
    plt.show()

    calib_file.close()