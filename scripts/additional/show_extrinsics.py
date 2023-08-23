from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import numpy as np
from scripts import helpers

#extrinsic_file = open("/home/ypollet/Numerisation/Sphaeroptica/lysandra_bellargus/jpegs/ext.json")
#extrinsic_file = open("/home/ypollet/Numerisation/Sphaeroptica/Sphaeroptica/data/geonemus-geoffroyii/extrinsics.json")
#extrinsic_file = open("/home/ypollet/Numerisation/Sphaeroptica/lysandra_bellargus/extrinsics.json")
extrinsic_file = open("/home/ypollet/lys_median/ext.json")

extrinsics = json.load(extrinsic_file)


fig = plt.figure()
ax = plt.axes(projection='3d')

ax.scatter([0], [0], [0], color="black", label='center')

for image in extrinsics:
    print(image)
    matrix = np.matrix(extrinsics[image]["matrix"])
    rotation = matrix[0:3,0:3]
    trans = matrix[0:3,3]

    C = helpers.get_camera_world_coordinates(rotation, trans)
    ax.scatter(C.item(0), C.item(1), C.item(2), color="blue")

    ray_x = (rotation[0]).T
    ax.quiver(C.item(0), C.item(1), C.item(2), ray_x.item(0), ray_x.item(1), ray_x.item(2), length=0.03, color="red")
    ray_y = (rotation[1]).T
    ax.quiver(C.item(0), C.item(1), C.item(2), ray_y.item(0), ray_y.item(1), ray_y.item(2), length=0.03, color="blue")
    ray_z = (rotation[2]).T
    ax.quiver(C.item(0), C.item(1), C.item(2), ray_z.item(0), ray_z.item(1), ray_z.item(2), length=0.03, color="green")
'''
ax.set_xlim3d(-0.3, 0.3)
ax.set_ylim3d(-0.3, 0.3)
ax.set_zlim3d(-0.22, 0.22)'''
plt.show()

extrinsic_file.close()