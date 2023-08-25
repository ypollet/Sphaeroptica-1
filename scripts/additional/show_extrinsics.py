import sys
 
# setting path
sys.path.append('/home/psadmin/Sphaeroptica/')

from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import numpy as np
from scripts import helpers, reconstruction

#extrinsic_file = open("/home/ypollet/Numerisation/Sphaeroptica/lysandra_bellargus/jpegs/ext.json")
#extrinsic_file = open("/home/ypollet/Numerisation/Sphaeroptica/Sphaeroptica/data/geonemus-geoffroyii/extrinsics.json")
#extrinsic_file = open("/home/ypollet/Numerisation/Sphaeroptica/lysandra_bellargus/extrinsics.json")
calib_file = open("/home/psadmin/scAnt/calib_stacked/calibration_intrinsics.json")

calib = json.load(calib_file)
intrinsics = np.matrix(calib["intrinsics"]["camera matrix"]["matrix"])
cx, cy = intrinsics.item(0,2), intrinsics.item(1,2)

dist_coeffs = np.matrix(calib["intrinsics"]["distortion matrix"]["matrix"])
extrinsics = calib["extrinsics"]


fig = plt.figure()
ax = plt.axes(projection='3d')


dist = 0
center = np.array([[0],[0],[0]])

proj_points = []
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

    img_point_undistort = reconstruction.undistort_iter(np.array([cx, cy]).reshape((1,1,2)), intrinsics, dist_coeffs)

    proj_mat = np.matmul(intrinsics, matrix)
    proj_point = helpers.ProjPoint(proj_mat, img_point_undistort)
    proj_points.append(proj_point)

center = reconstruction.triangulate_point(proj_points)[:3]
print(center)

ax.scatter(center.item(0), center.item(1), center.item(2), color="black", label='center')

for image in extrinsics:
    image_ext = np.matrix(extrinsics[image]["matrix"])
    image_ext = image_ext[0:3, 0:4]

    rotation = image_ext[0:3, 0:3]
    trans = np.array(image_ext[0:3, 3].T).squeeze()
    trans_w = np.array(helpers.get_camera_world_coordinates(rotation, trans)).squeeze()
    dist += reconstruction.get_distance(center, trans_w) + 0.0115

avg_dist = dist/len(extrinsics)
print("avg dist = ", avg_dist)
'''
ax.set_xlim3d(-0.3, 0.3)
ax.set_ylim3d(-0.3, 0.3)
ax.set_zlim3d(-0.22, 0.22)'''
plt.show()

calib_file.close()